#!/bin/bash

# Script to clean up test failure scenarios

echo "Cleaning up test failure scenarios..."

# Delete all test deployments
kubectl delete deployment test-crashloopbackoff -n default --ignore-not-found=true
kubectl delete deployment test-imagepullbackoff -n default --ignore-not-found=true
kubectl delete deployment test-oomkilled -n default --ignore-not-found=true
kubectl delete deployment test-app -n default --ignore-not-found=true

# Delete test service
kubectl delete service test-service -n default --ignore-not-found=true

echo "Test scenarios cleaned up."
