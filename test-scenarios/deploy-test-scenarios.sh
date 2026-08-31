#!/bin/bash

# Script to deploy test failure scenarios for testing the AI Kubernetes Agent

echo "Deploying test failure scenarios..."

# Deploy CrashLoopBackOff scenario
echo "1. Deploying CrashLoopBackOff scenario..."
kubectl apply -f crashloopbackoff-deployment.yaml

# Deploy ImagePullBackOff scenario
echo "2. Deploying ImagePullBackOff scenario..."
kubectl apply -f imagepullbackoff-deployment.yaml

# Deploy OOMKilled scenario
echo "3. Deploying OOMKilled scenario..."
kubectl apply -f oomkilled-deployment.yaml

# Deploy Service Selector Mismatch scenario
echo "4. Deploying Service Selector Mismatch scenario..."
kubectl apply -f service-selector-mismatch.yaml

echo "Waiting for pods to be created..."
sleep 10

echo "Test scenarios deployed. Current pod status:"
kubectl get pods -n default

echo ""
echo "To clean up test scenarios, run: ./cleanup-test-scenarios.sh"
