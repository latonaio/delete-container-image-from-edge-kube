from aion.logger import lprint
from kubernetes import client
from kubernetes.client.rest import ApiException
from controllers.kubernetes_controller import KubernetesController


class PvcController(KubernetesController):
    def __init__(self):
        super().__init__()

    def set_client(self):
        self._set_conf()
        self.k8s_v1 = client.CoreV1Api(client.ApiClient(self.configuration))

    def apply(self, name, path, storage, namespace):
        if storage is None:
            storage = "1Gi"

        try:
            is_pvc = self._is_pvc(name, namespace)
            if is_pvc is False:
                self._create_pv(name, path, storage, namespace)
                return self._create_pvc(name, storage, namespace)

            # if self._delete_pvc(name, namespace):
            #     time.sleep(5)
            #     self._create_pv(name, path, storage, namespace)
            #     return self._create_pvc(name, storage, namespace)
        except ApiException as e:
            lprint(e)
            raise RuntimeError(e)

    def _is_pvc(self, name, namespace):
        try:
            ret = self.k8s_v1.list_namespaced_persistent_volume_claim(namespace)
            for item in ret.items:
                if item.metadata.name == name:
                    return True
            return False
        except ApiException as e:
            lprint(e)
            raise RuntimeError(e)

    def _create_pvc(self, name, storage, namespace):
        body = self._get_pvc_body(name, storage, namespace)

        try:
            return self.k8s_v1.create_namespaced_persistent_volume_claim(namespace, body)
        except ApiException as e:
            lprint(e)
            raise RuntimeError(e)

    def _create_pv(self, name, path, storage, namespace):
        body = self._get_pv_body(name, path, storage, namespace)

        try:
            return self.k8s_v1.create_persistent_volume(body)
        except ApiException as e:
            lprint(e)
            raise RuntimeError(e)

    def delete_pvc(self, name, namespace):
        if namespace == "default":
            self.k8s_v1.delete_persistent_volume(name)
        else:
            self.k8s_v1.delete_persistent_volume(name + "-" + namespace)
        return self.k8s_v1.delete_namespaced_persistent_volume_claim(name, namespace)

    def _get_pvc_body(self, name, storage, namespace):
        spec = self._get_spec_pvc(name, storage)

        return client.V1PersistentVolumeClaim(
            api_version="v1",
            kind="PersistentVolumeClaim",
            metadata=client.V1ObjectMeta(name=name, namespace=namespace),
            spec=spec
        )

    # can not specify namespace in PV. so add suffix namespace with PV name
    def _get_pv_body(self, name, path, storage, namespace):
        spec = self._get_pv_spec(name, path, storage)
        if namespace != "default":
            name = name + "-" + namespace

        return client.V1PersistentVolume(
            api_version="v1",
            kind="PersistentVolume",
            metadata=client.V1ObjectMeta(name=name),
            spec=spec
        )

    def _get_spec_pvc(self, name, storage):
        return client.V1PersistentVolumeClaimSpec(
            storage_class_name=name,
            access_modes=["ReadWriteOnce"],
            resources=client.V1ResourceRequirements(
                requests={"storage": storage}
            )
        )

    def _get_pv_spec(self, name, path, storage):
        return client.V1PersistentVolumeSpec(
            storage_class_name=name,
            access_modes=["ReadWriteOnce"],
            capacity={"storage": storage},
            host_path=client.V1HostPathVolumeSource(
                path=path
            )
        )
