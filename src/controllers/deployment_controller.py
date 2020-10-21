import time

from aion.logger import lprint
from kubernetes import client
from kubernetes.client.rest import ApiException

from controllers.const import VOLUME_TYPE_PVC, VOLUME_TYPE_HOST_PATH
from controllers.kubernetes_controller import KubernetesController


class DeploymentController(KubernetesController):
    def __init__(self):
        super().__init__()

    def set_client(self):
        self._set_conf()
        self.k8s_apps_v1 = client.AppsV1Api(client.ApiClient(self.configuration))
        self.k8s_v1 = client.CoreV1Api(client.ApiClient(self.configuration))

    def apply(self, name, image_name, container_port, envs, volume_mounts, volumes, service_account_name,
              prior_device_name, namespace):
        try:
            is_deployment = self._is(name, namespace)
            if is_deployment:
                return self._update(image_name, name, container_port, envs, volume_mounts, volumes,
                                    service_account_name, prior_device_name, namespace)

            return self._create(image_name, name, container_port, envs, volume_mounts, volumes, service_account_name,
                                prior_device_name, namespace)
        except ApiException as e:
            lprint(e)
            raise RuntimeError(e)

    def _is(self, name, namespace):
        try:
            ret = self.k8s_apps_v1.list_namespaced_deployment(namespace)
            for item in ret.items:
                if item.metadata.name == name:
                    return True
            return False
        except ApiException as e:
            lprint(e)
            raise RuntimeError(e)

    def _create(self, image_name, name, container_port, envs, volume_mounts, volumes, service_account_name,
                prior_device_name, namespace):
        body = self._get_body(image_name, name, container_port, envs, volume_mounts, volumes, service_account_name,
                              prior_device_name, namespace)

        try:
            ret = self.k8s_apps_v1.create_namespaced_deployment(namespace, body)
            return ret
        except ApiException as e:
            lprint(e)
            raise RuntimeError(e)

    def _update(self, image_name, name, container_port, envs, volume_mounts, volumes, service_account_name,
                prior_device_name, namespace):
        body = self._get_body(image_name, name, container_port, envs, volume_mounts, volumes, service_account_name,
                              prior_device_name, namespace)

        try:
            return self.k8s_apps_v1.replace_namespaced_deployment(name, namespace, body)
        except ApiException as e:
            lprint(e)
            raise RuntimeError(e)

    def _get_body(self, image_name, name, container_port, envs, volume_mounts, volumes, service_account_name,
                  prior_device_name, namespace):
        pod_template = self._get_pod_template(image_name, name, container_port, envs, volume_mounts, volumes,
                                              service_account_name, prior_device_name)

        return client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=name, namespace=namespace),
            spec=client.V1DeploymentSpec(
                replicas=1,
                template=pod_template,
                selector={'matchLabels': {"run": name}}
            )
        )

    def is_pod_with_retry(self, name, namespace):
        pod_running = self._is_pod(name, namespace)
        if pod_running:
            return True

        for i in range(self.retry_cnt):
            lprint("retrying in 5 seconds...")
            time.sleep(5)
            pod_running = self._is_pod(name, namespace)
            if pod_running:
                return True

        return False

    def _is_pod(self, name, namespace):
        try:
            ret = self.k8s_v1.list_namespaced_pod(namespace)
            if ret is None:
                return False

            for pod in ret.items:
                if name not in pod.metadata.name:
                    continue

                if pod.status.container_statuses is None:
                    continue

                for status in pod.status.container_statuses:
                    if status.ready:
                        return True
            return False
        except ApiException as e:
            raise RuntimeError(e)

    def _get_pod_template(self, image_name, name, container_port, envs, volume_mounts, volumes, service_account_name,
                          prior_device_name):
        env_list = self._get_envs(envs)
        volume_mount_list = self._get_volume_mounts(volume_mounts)
        volume_list = self._get_volumes(volumes)
        image_pull_secret_name = prior_device_name + "-registry"

        if container_port != None and container_port != "":
            return client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(labels={"run": name}),
                spec=client.V1PodSpec(
                    service_account_name=service_account_name,
                    image_pull_secrets=[client.V1LocalObjectReference(
                        name=image_pull_secret_name
                    )],
                    containers=[client.V1Container(
                        name=name,
                        image=image_name,
                        image_pull_policy="Always",
                        ports=[client.V1ContainerPort(container_port=int(container_port))],
                        env=env_list,
                        volume_mounts=volume_mount_list
                    )],
                    volumes=volume_list
                )
            )

        return client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"run": name}),
            spec=client.V1PodSpec(
                service_account_name=service_account_name,
                image_pull_secrets=[client.V1LocalObjectReference(
                    name=image_pull_secret_name
                )],
                containers=[client.V1Container(
                    name=name,
                    image=image_name,
                    image_pull_policy="Always",
                    env=env_list,
                    volume_mounts=volume_mount_list
                )],
                volumes=volume_list
            )
        )

    def _get_envs(self, env):
        envs = []
        if env != None and env != "":
            for name, item in env.items():
                envs.append(client.V1EnvVar(
                    name=name,
                    value=item
                ))

        return envs

    def _get_volume_mounts(self, volume_mounts):
        volume_mount_list = []
        if volume_mounts != None and volume_mounts != "":
            for name, path in volume_mounts.items():
                volume_mount_list.append(client.V1VolumeMount(
                    name=name,
                    mount_path=path
                ))

        return volume_mount_list

    def _get_volumes(self, volumes):
        volume_list = []
        if volumes != None and volumes != "":
            for name, item in volumes.items():
                if item.get("type") == VOLUME_TYPE_PVC:
                    volume_list.append(client.V1Volume(
                        name=name,
                        persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                            claim_name=name
                        )
                    ))
                elif item.get("type") == VOLUME_TYPE_HOST_PATH:
                    volume_list.append(client.V1Volume(
                        name=name,
                        host_path=client.V1HostPathVolumeSource(
                            path=item.get("path")
                        )
                    ))

    def delete(self, name, namespace):
        return self.k8s_apps_v1.delete_namespaced_deployment(name, namespace)
