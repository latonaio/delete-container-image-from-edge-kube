import os

from kubernetes import client


class KubernetesController():
    def __init__(self):
        self.configuration = ""
        self.retry_cnt = 5

    def _set_conf(self):
        configuration = client.Configuration()
        configuration.verify_ssl = True
        configuration.host = "https://" + os.environ.get("KUBERNETES_SERVICE_HOST")
        configuration.api_key["authorization"] = self._get_token()
        configuration.api_key_prefix["authorization"] = "Bearer"
        configuration.ssl_ca_cert = "/var/run/secrets/kubernetes.io/serviceaccount/ca.crt"
        self.configuration = configuration

    def _get_token(self):
        with open("/var/run/secrets/kubernetes.io/serviceaccount/token") as f:
            return f.read()
