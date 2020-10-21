#!/bin/bash

kubectl exec -it $(kubectl get po | awk '{print $1}' | grep -v NAME | grep delete-container-image-from-edge) -- python3 src/main.py