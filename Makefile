apply:
	kubectl apply -f k8s/delete-container-image-from-edge-kube/

delete:
	kubectl delete -f k8s/delete-container-image-from-edge-kube/
	kubectl delete deployment nginx-deployment
	sudo rm -rf delete_container_image_from_edge_kube/__pycache__/

exec:
	sh shell/exec.sh

do:
	sh shell/do.sh

redo:
	-kubectl delete deployment nginx-deployment
	-sudo rm -rf delete_container_image_from_edge_kube/__pycache__/
	sleep 5
	sh shell/do.sh

build:
	sh docker-build.sh