import os

import docker
from aion.logger import lprint


class DockerController:
    def __init__(self):
        self.client = docker.DockerClient(base_url='unix://var/run/docker.sock')
        self.local_registry_addr = "localhost:31112"
        self.local_image_name = ""

    def login(self):
        username = os.environ.get("REGISTRY_USER")
        password = os.environ.get("REGISTRY_PASSWORD")
        self.client.login(
            username=username, password=password, registry=self.local_registry_addr)

    def tag(self, remote_image_name, name, docker_tag):
        image = self.client.images.get(remote_image_name)
        self.local_image_name = self.local_registry_addr + '/' + name + ":" + docker_tag
        image.tag(self.local_image_name)

    def push(self):
        try:
            lprint(self.local_image_name)
            ret = self.client.images.push(self.local_image_name)
            if "err" in ret:
                return False

            lprint(ret)
            return True
        except docker.errors.APIError as e:
            lprint(e)
            raise RuntimeError(e)

    def remove_image(self, microservice_name, ip, port, docker_tag):
        self.client.images.remove(f"{ip}:{port}/{microservice_name}:{docker_tag}", force=True)
        self.client.images.remove(f"{self.local_registry_addr}/{microservice_name}:{docker_tag}", force=True)
