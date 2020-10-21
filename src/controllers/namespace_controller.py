from aion.logger import lprint
from kubernetes import client
from kubernetes.client.rest import ApiException

from controllers.kubernetes_controller import KubernetesController


class NamespaceController(KubernetesController):
    def __init__(self):
        super().__init__()

    def set_client(self):
        self._set_conf()
        self.k8s_v1 = client.CoreV1Api(client.ApiClient(self.configuration))

    def apply(self, name):
        try:
            is_namespace = self._is(name)
            if is_namespace is False:
                return self._create(name)
        except ApiException as e:
            lprint(e)
            raise RuntimeError(e)

    def _is(self, name):
        try:
            ret = self.k8s_v1.list_namespace()
            for item in ret.items:
                if item.metadata.name == name:
                    return True
            return False
        except ApiException as e:
            lprint(e)
            raise RuntimeError(e)

    def _create(self, name):
        try:
            ret = self.k8s_v1.create_namespace(client.V1Namespace(
                api_version="v1",
                kind="Namespace",
                metadata=client.V1ObjectMeta(name=name)
            ))
            return ret
        except ApiException as e:
            lprint(e)
            raise RuntimeError(e)
