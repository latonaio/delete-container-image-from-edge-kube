from aion.logger import lprint
from kubernetes import client
from kubernetes.client.rest import ApiException

from controllers.kubernetes_controller import KubernetesController

SERVICE_TYPE_CLUSTER_IP = "ClusterIP"
SERVICE_TYPE_NODE_PORT = "NodePort"


class ServiceController(KubernetesController):
    def __init__(self):
        super().__init__()

    def set_client(self):
        self._set_conf()
        self.k8s_v1 = client.CoreV1Api(client.ApiClient(self.configuration))

    def apply(self, name, container_port, node_port, namespace):
        try:
            is_service = self._is(name, namespace)
            if is_service is False:
                return self._create(name, container_port, node_port, namespace)

            if self.delete(name, namespace):
                return self._create(name, container_port, node_port, namespace)

        except ApiException as e:
            lprint(e)
            raise RuntimeError(e)

    def _is(self, name, namespace):
        try:
            ret = self.k8s_v1.list_namespaced_service(namespace)
            for item in ret.items:
                if item.metadata.name == name:
                    return True
            return False
        except ApiException as e:
            lprint(e)
            raise RuntimeError(e)

    def _create(self, name, container_port, node_port, namespace):
        body = self._get_body(name, container_port, node_port, namespace)

        try:
            return self.k8s_v1.create_namespaced_service(namespace, body)
        except ApiException as e:
            lprint(e)
            raise RuntimeError(e)

    def delete(self, name, namespace):
        return self.k8s_v1.delete_namespaced_service(name, namespace)

    def _get_body(self, name, container_port, node_port, namespace):
        spec = self._get_spec(name, container_port, node_port)

        return client.V1Service(
            api_version="v1",
            kind="Service",
            metadata=client.V1ObjectMeta(name=name, namespace=namespace),
            spec=spec
        )

    def _get_spec(self, name, container_port, node_port):
        selector = {"run": name}
        service_type = SERVICE_TYPE_CLUSTER_IP
        if node_port:
            service_type = SERVICE_TYPE_NODE_PORT

        ports = []
        if service_type == SERVICE_TYPE_CLUSTER_IP:
            ports = [
                {
                    "name": name,
                    "port": int(container_port)
                }
            ]
        elif service_type == SERVICE_TYPE_NODE_PORT:
            ports = [
                {
                    "name": name,
                    "port": int(container_port),
                    "targetPort": int(container_port),
                    "nodePort": int(node_port)
                }
            ]

        return client.V1ServiceSpec(
            selector=selector,
            type=service_type,
            ports=ports
        )
