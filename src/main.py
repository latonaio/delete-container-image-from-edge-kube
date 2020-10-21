import logging
import time
import traceback

from aion.logger import lprint, initialize_logger
from aion.microservice import Options, main_decorator

from controllers.const import SERVICE_NAME, KUBERNETES_PACKAGE, SUCCEED_STATUS_INDEX, FAILED_STATUS_INDEX, \
    VOLUME_TYPE_PVC, DELETED_STATUS_INDEX
from controllers.deployment_controller import DeploymentController
from controllers.docker_controller import DockerController
from controllers.docker_registry_controller import DockerRegistryController
from controllers.pvc_controller import PvcController
from controllers.service_controller import ServiceController

METADATA_KEYS = [
    "priorDeviceName",
    "deviceName",
    "projectName",
    "projectCommitId",
    "ip",
    "port",
    "microserviceName",
    "dockerTag"
]


@main_decorator(SERVICE_NAME)
def main(opt: Options):
    initialize_logger(SERVICE_NAME)
    logging.getLogger(KUBERNETES_PACKAGE).setLevel(logging.ERROR)

    conn = opt.get_conn()
    num = opt.get_number()
    kanban = conn.get_one_kanban(SERVICE_NAME, num)
    metadata = kanban.get_metadata()

    lprint("metadata: ", metadata)

    for key in METADATA_KEYS:
        if key not in metadata:
            raise RuntimeError(f"Not found '{key}' in metadadata.")

    deployment_name = metadata.get("microserviceName")
    docker_tag = metadata.get("dockerTag")
    remote_ip = metadata.get("ip")
    remote_port = metadata.get("port")
    container_port = metadata.get("containerPort")
    volumes = metadata.get("volumes")
    prior_device_name = metadata.get("priorDeviceName")
    namespace = metadata.get("projectName").lower()

    try:
        lprint("==========DELETE pvc==========")
        # pvc
        if volumes != None and volumes != "":
            pvc_controller = PvcController()
            for name, item in volumes.items():
                if item.get("type") == VOLUME_TYPE_PVC:
                    try:
                        pvc_controller.set_client()
                        pvc_controller.delete_pvc(name, namespace)
                    except Exception as e:
                        lprint(f"[info]pvc is not deleted (name: {name})")
                        lprint(e)

        lprint("==========DELETE deployment==========")
        # deployment
        try:
            deployment_controller = DeploymentController()
            deployment_controller.set_client()
            deployment_controller.delete(deployment_name, namespace)
        except Exception as e:
            lprint(f"[info]deployment is not deleted (name: {deployment_name})")
            lprint(e)

        lprint("==========DELETE service==========")
        # service
        if container_port != None and container_port != "":
            try:
                service_controller = ServiceController()
                service_controller.set_client()
                service_controller.delete(deployment_name, namespace)
            except Exception as e:
                lprint(f"[info]service is not deleted (name: {deployment_name})")
                lprint(e)

        # デプロイ元でカンバンが滞留する問題を防ぐ
        time.sleep(10)

        metadata['status'] = DELETED_STATUS_INDEX
        metadata['error'] = ""

        conn.output_kanban(
            metadata=metadata,
            device_name=prior_device_name
        )

        time.sleep(30)

        lprint("==========DELETE image from host==========")
        # remove image from host
        try:
            docker_controller = DockerController()
            docker_controller.remove_image(
                microservice_name=deployment_name,
                ip=remote_ip,
                port=remote_port,
                docker_tag=docker_tag
            )
        except Exception as e:
            lprint(f"[info]local image is not removed (name: {deployment_name})")
            lprint(e)

        lprint("==========DELETE image from docker registry==========")
        try:
            docker_registry_controller = DockerRegistryController()
            image_digest = docker_registry_controller.get_digest(
                repository_name=deployment_name,
                image_tag=docker_tag
            )

            lprint(f'digest is {image_digest}')
            docker_registry_controller.delete_tag_from_docker_registry(
                repository_name=deployment_name,
                digest=image_digest
            )
        except Exception as e:
            lprint(f"[info]registry image is not removed (name: {deployment_name})")
            lprint(e)

        metadata['status'] = SUCCEED_STATUS_INDEX
        metadata['error'] = ""

        conn.output_kanban(
            metadata=metadata,
            device_name=prior_device_name
        )

        return

    except Exception:
        lprint(traceback.format_exc())
        metadata['status'] = FAILED_STATUS_INDEX
        metadata['error'] = ""
        conn.output_kanban(
            metadata=metadata,
            device_name=prior_device_name
        )


if __name__ == "__main__":
    main()
