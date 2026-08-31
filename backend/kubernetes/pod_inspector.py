from typing import Dict, Any, List
from loguru import logger
import os
import sys

# Add backend directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    from kubectl.kubectl_executor import KubectlExecutor
except ImportError as e:
    logger.error(f"Failed to import KubectlExecutor: {e}")
    raise


class PodInspector:
    """Inspects Kubernetes pods for health issues."""
    
    # Unhealthy pod statuses to detect
    UNHEALTHY_STATUSES = [
        "CrashLoopBackOff",
        "ImagePullBackOff",
        "Pending",
        "Error",
        "OOMKilled",
        "ContainerCreating"
    ]
    
    def __init__(self, kubectl_executor: KubectlExecutor):
        """
        Initialize pod inspector.
        
        Args:
            kubectl_executor: KubectlExecutor instance
        """
        self.kubectl = kubectl_executor
    
    def inspect_pods(self, namespace: str = "all") -> Dict[str, Any]:
        """
        Inspect pods across all or specific namespace.
        
        Args:
            namespace: Namespace to inspect ("all" for all namespaces)
            
        Returns:
            Dictionary with pod health status and problematic pods
        """
        logger.info(f"Inspecting pods in namespace: {namespace}")
        
        # Build kubectl command
        ns_flag = "-A" if namespace == "all" else f"-n {namespace}"
        command = f"get pods {ns_flag} -o json"
        
        result = self.kubectl.execute_json(command)
        
        if not result["success"]:
            logger.error(f"Failed to get pods: {result['error']}")
            return {
                "healthy": False,
                "error": result["error"],
                "problematic_pods": []
            }
        
        pods_data = result["data"]
        problematic_pods = []
        
        # Process each pod
        for item in pods_data.get("items", []):
            pod_name = item.get("metadata", {}).get("name", "unknown")
            pod_namespace = item.get("metadata", {}).get("namespace", "unknown")
            
            # Get pod phase
            pod_phase = item.get("status", {}).get("phase", "Unknown")
            
            # Check container statuses for more detailed info
            container_statuses = item.get("status", {}).get("containerStatuses", [])
            
            # Check for unhealthy conditions
            is_unhealthy = False
            status_details = pod_phase
            
            for container_status in container_statuses:
                # Check waiting state
                waiting = container_status.get("waiting", {})
                if waiting:
                    reason = waiting.get("reason", "")
                    if reason in self.UNHEALTHY_STATUSES:
                        is_unhealthy = True
                        status_details = reason
                        break
                
                # Check terminated state
                terminated = container_status.get("terminated", {})
                if terminated:
                    reason = terminated.get("reason", "")
                    if reason == "OOMKilled":
                        is_unhealthy = True
                        status_details = "OOMKilled"
                        break
                
                # Check last termination state
                last_terminated = container_status.get("lastState", {}).get("terminated", {})
                if last_terminated:
                    reason = last_terminated.get("reason", "")
                    if reason == "OOMKilled":
                        is_unhealthy = True
                        status_details = "OOMKilled"
                        break
            
            # Check phase directly
            if pod_phase in self.UNHEALTHY_STATUSES:
                is_unhealthy = True
                status_details = pod_phase
            
            # Check if pod is stuck in ContainerCreating
            if pod_phase == "Running" and not container_statuses:
                is_unhealthy = True
                status_details = "ContainerCreating"
            
            if is_unhealthy:
                problematic_pods.append({
                    "name": pod_name,
                    "namespace": pod_namespace,
                    "status": status_details,
                    "phase": pod_phase
                })
                logger.warning(f"Found unhealthy pod: {pod_name} in {pod_namespace} - {status_details}")
        
        is_healthy = len(problematic_pods) == 0
        
        logger.info(f"Pod inspection complete. Healthy: {is_healthy}, Problematic pods: {len(problematic_pods)}")
        
        return {
            "healthy": is_healthy,
            "problematic_pods": problematic_pods,
            "total_inspected": len(pods_data.get("items", []))
        }
    
    def get_pod_details(self, pod_name: str, namespace: str = "default") -> Dict[str, Any]:
        """
        Get detailed information about a specific pod.
        
        Args:
            pod_name: Name of the pod
            namespace: Namespace of the pod
            
        Returns:
            Dictionary with pod details
        """
        command = f"get pod {pod_name} -n {namespace} -o json"
        result = self.kubectl.execute_json(command)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result["error"]
            }
        
        return {
            "success": True,
            "data": result["data"]
        }
