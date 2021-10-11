import os

import pycurl
import simplejson

SELF_IP = 'localhost'

USERNAME = os.environ.get("REGISTRY_USER")
PASSWORD = os.environ.get("REGISTRY_PASSWORD")


class DockerRegistryController():
    def __init__(self):
        self.local_registry_inner_addr = "kube-registry:5000"
        self.local_image_name = ""

    def remove_from_docker_registry(self, repository_name, docker_tag):
        '''
        docker registryからのtagの削除

        @param repository_name: リポジトリ名(image名)
        @param docker_tag: タグ名
        @return: docker registryのdeleteAPIから返されたレスポンス
        '''
        digest = self.get_digest(repository_name, docker_tag)

        if digest is None:
            print(f"[error] failed to get digest form docker registry)")
            raise

        print(f"[info] remove from docker registry(digest: {digest})")
        result = self.delete_tag_from_docker_registry(repository_name, digest)

        if 'errors' in result:
            print(f"[error] failed to remove from docker registry (error: {result['errors']})")
            raise

        return result

    def get_digest(self, repository_name, image_tag):
        '''
        docker registryのAPIをコールしてimageのdigestを取得する

        @param repository_name: リポジトリ名(image名)
        @param image_tag: タグ名
        @return: docker registry APIからのレスポンス
        '''
        curl = pycurl.Curl()
        curl.setopt(pycurl.URL,
                    f'https://{self.local_registry_inner_addr}/v2/{repository_name}/manifests/{image_tag}')
        curl.setopt(pycurl.USERPWD, '%s:%s' % (USERNAME, PASSWORD))
        curl.setopt(pycurl.HTTPHEADER, ["Accept: application/vnd.docker.distribution.manifest.v2+json"])
        curl.setopt(pycurl.SSL_VERIFYPEER, 0)
        curl.setopt(pycurl.SSL_VERIFYHOST, 0)

        header = ManifestHeader()
        curl.setopt(pycurl.HEADERFUNCTION, header.store)
        curl.perform()

        return header.get_digest()

    def delete_tag_from_docker_registry(self, repository_name, digest):
        '''
        docker registryのAPIをコールしてdocker registry上のtagを削除する

        @param repository_name: リポジトリ名(image名)
        @param digest: imageのcontent digest
        @return: docker registry APIからのレスポンス
        '''
        url = f'https://{self.local_registry_inner_addr}/v2/{repository_name}/manifests/{digest}'

        curl = pycurl.Curl()
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.CUSTOMREQUEST, 'DELETE')
        curl.setopt(pycurl.USERPWD, '%s:%s' % (USERNAME, PASSWORD))
        curl.setopt(pycurl.SSL_VERIFYPEER, 0)
        curl.setopt(pycurl.SSL_VERIFYHOST, 0)

        response = simplejson.loads(curl.perform_rs())
        curl.close()

        return response


class ManifestHeader():
    def __init__(self):
        self.headers = []

    def store(self, b):
        self.headers.append(b.decode('utf-8'))

    def get_digest(self):
        digest_header = next(filter(lambda h: h.startswith("Docker-Content-Digest:"), self.headers), None)
        # 23 -> len("Docker-Content-Digest: ")
        # 94 -> end of digest

        # e.g. sha256:XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
        return digest_header[23:94] if digest_header is not None else None
