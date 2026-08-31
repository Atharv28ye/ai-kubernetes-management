# AI Kubernetes Agent - Testing Guide

## Overview
The AI Kubernetes Agent is now fully integrated and ready for end-to-end testing. This guide covers testing procedures for all components.

## Prerequisites
- Backend server running on http://localhost:8000
- Frontend server running on http://localhost:3000
- Kubernetes cluster accessible (Minikube, Docker Desktop, or cloud cluster)
- kubectl configured with cluster access

## Test Scenarios

### 1. Cluster Selection Test
**Goal:** Verify cluster selection from kubeconfig works correctly

**Steps:**
1. Open dashboard at http://localhost:3000
2. Check that the cluster selector shows available clusters from kubeconfig
3. Select a different cluster (if available)
4. Verify the current context indicator updates

**Expected Result:**
- Cluster dropdown shows all contexts from kubeconfig
- Current cluster is highlighted
- Switching clusters updates the current context

### 2. Healthy Cluster Test
**Goal:** Verify the system handles healthy clusters gracefully

**Steps:**
1. Select a healthy cluster
2. Click "Investigate Cluster"
3. Wait for investigation to complete

**Expected Result:**
- Progress updates show each step completing
- Green "Cluster is Healthy" message appears
- No errors are shown
- Investigation history is updated

### 3. Kubernetes Connection Error Test
**Goal:** Verify error handling when cluster is unreachable

**Steps:**
1. Temporarily break kubectl access (e.g., wrong kubeconfig)
2. Click "Investigate Cluster"

**Expected Result:**
- Friendly error message appears
- No ugly stack traces
- Clear guidance on how to fix the issue

### 4. Test Failure Scenarios

#### Scenario 1: CrashLoopBackOff
**Deploy:**
```bash
cd test-scenarios
kubectl apply -f crashloopbackoff-deployment.yaml
```

**Expected AI Analysis:**
- Root Cause: Missing environment variable
- Fix: Add DATABASE_URL environment variable
- kubectl command: `kubectl edit deployment test-crashloopbackoff`

#### Scenario 2: ImagePullBackOff
**Deploy:**
```bash
kubectl apply -f imagepullbackoff-deployment.yaml
```

**Expected AI Analysis:**
- Root Cause: Invalid image repository/tag
- Fix: Update deployment with correct image
- kubectl command: `kubectl set image deployment/test-imagepullbackoff nginx=nginx:latest`

#### Scenario 3: OOMKilled
**Deploy:**
```bash
kubectl apply -f oomkilled-deployment.yaml
```

**Expected AI Analysis:**
- Root Cause: Container exceeded memory limit
- Fix: Increase memory requests/limits
- kubectl command: `kubectl edit deployment test-oomkilled`

#### Scenario 4: Service Selector Mismatch
**Deploy:**
```bash
kubectl apply -f service-selector-mismatch.yaml
```

**Expected AI Analysis:**
- Root Cause: Service selector doesn't match pod labels
- Fix: Update service selector to match deployment labels
- kubectl command: `kubectl edit service test-service`

**Cleanup:**
```bash
cd test-scenarios
./cleanup-test-scenarios.sh
```

### 5. Authentication Test
**Goal:** Verify InsForge authentication works

**Steps:**
1. Check that InsForge credentials are configured
2. Sign up/in via the dashboard
3. Verify user session persists
4. Run an investigation
5. Check investigation history

**Expected Result:**
- Authentication flow works smoothly
- User stays logged in
- Investigations are saved to history

### 6. Realtime Progress Test
**Goal:** Verify realtime progress updates work

**Steps:**
1. Start an investigation
2. Watch the progress indicator
3. Verify steps update in real-time

**Expected Result:**
- Progress updates appear as investigation progresses
- "Live" indicator shows when realtime is active
- All investigation steps are shown

### 7. Empty States Test
**Goal:** Verify proper empty states are shown

**Test Cases:**
- No clusters in kubeconfig
- No investigations in history
- Investigation completes with no issues found

**Expected Result:**
- Friendly messages guide users
- No confusing empty screens
- Clear next steps are provided

## API Testing

### Test Investigation API
```bash
# Basic investigation
curl -X POST http://localhost:8000/investigate/ \
  -H "Content-Type: application/json" \
  -d '{"namespace": "all", "collect_logs": false, "enable_ai": false}'

# With AI enabled (requires OPENROUTER_API_KEY)
curl -X POST http://localhost:8000/investigate/ \
  -H "Content-Type: application/json" \
  -d '{"namespace": "all", "collect_logs": true, "enable_ai": true}'

# Quick investigation
curl -X POST http://localhost:8000/investigate/quick?namespace=default&enable_ai=false

# Targeted investigation
curl -X POST http://localhost:8000/investigate/targeted \
  -H "Content-Type: application/json" \
  -d '{"resource_name": "test-pod", "resource_type": "pod", "namespace": "default", "enable_ai": false}'
```

### Test Clusters API
```bash
# Get available clusters
curl http://localhost:8000/clusters/

# Switch cluster context
curl -X POST http://localhost:8000/clusters/switch \
  -H "Content-Type: application/json" \
  -d '{"context_name": "minikube"}'
```

## Performance Testing

### Load Test
Run multiple concurrent investigations to test system performance:
```bash
for i in {1..5}; do
  curl -X POST http://localhost:8000/investigate/ \
    -H "Content-Type: application/json" \
    -d '{"namespace": "all", "collect_logs": false, "enable_ai": false}' &
done
wait
```

## Validation Checklist

- [ ] Cluster selection works correctly
- [ ] Healthy clusters show proper empty state
- [ ] Error messages are user-friendly
- [ ] Progress updates appear in real-time
- [ ] Authentication works end-to-end
- [ ] Investigation history is saved correctly
- [ ] AI reasoning provides accurate root cause analysis
- [ ] kubectl commands generated are actionable
- [ ] All test failure scenarios are detected correctly
- [ ] System handles cluster disconnection gracefully

## Troubleshooting

### Backend Issues
- Check backend logs: `backend/logs/app.log`
- Verify kubectl access: `kubectl get pods`
- Check environment variables are set correctly

### Frontend Issues
- Check browser console for errors
- Verify API_BASE_URL is correct
- Ensure InsForge credentials are configured

### Kubernetes Issues
- Verify cluster is running: `kubectl cluster-info`
- Check kubeconfig: `kubectl config view`
- Test kubectl access: `kubectl get pods -A`

## Next Steps

Once all tests pass:
1. Configure OPENROUTER_API_KEY for full AI functionality
2. Deploy to production environment
3. Set up monitoring and alerting
4. Create user documentation
5. Implement rate limiting for API endpoints
