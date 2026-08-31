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


class LogsCollector:
    """Collects logs from Kubernetes pods for troubleshooting."""
    
    # Patterns to look for in logs
    ERROR_PATTERNS = [
        "Exception",
        "Error",
        "Failed",
        "Connection refused",
        "Connection timeout",
        "Timeout",
        "Unable to connect",
        "Could not connect",
        "Missing",
        "Not found",
        "404",
        "500",
        "502",
        "503",
        "504"
    ]
    
    def __init__(self, kubectl_executor: KubectlExecutor, max_lines: int = 100):
        """
        Initialize logs collector.
        
        Args:
            kubectl_executor: KubectlExecutor instance
            max_lines: Maximum number of log lines to collect per pod
        """
        self.kubectl = kubectl_executor
        self.max_lines = max_lines
    
    def collect_logs(
        self,
        pod_name: str,
        namespace: str = "default",
        container: str = None,
        previous: bool = False
    ) -> Dict[str, Any]:
        """
        Collect logs from a specific pod.
        
        Args:
            pod_name: Name of the pod
            namespace: Namespace of the pod
            container: Optional container name (for multi-container pods)
            previous: Whether to fetch previous container logs
            
        Returns:
            Dictionary with logs and metadata
        """
        logger.info(f"Collecting logs for pod: {pod_name} in namespace: {namespace}")
        
        # Build kubectl logs command
        command = f"logs {pod_name} -n {namespace}"
        
        if container:
            command += f" -c {container}"
        
        if previous:
            command += " --previous"
        
        command += f" --tail={self.max_lines}"
        
        result = self.kubectl.execute(command)
        
        if not result["success"]:
            logger.error(f"Failed to collect logs for {pod_name}: {result['stderr']}")
            return {
                "success": False,
                "pod_name": pod_name,
                "namespace": namespace,
                "logs": "",
                "error": result["stderr"]
            }
        
        logs = result["stdout"]
        
        # Analyze logs for errors
        errors_found = self._analyze_logs(logs)
        
        logger.info(f"Collected {len(logs.splitlines())} lines from {pod_name}, found {len(errors_found)} potential errors")
        
        return {
            "success": True,
            "pod_name": pod_name,
            "namespace": namespace,
            "container": container,
            "logs": logs,
            "error_count": len(errors_found),
            "errors_found": errors_found[:10]  # Limit to top 10 errors
        }
    
    def _analyze_logs(self, logs: str) -> List[str]:
        """
        Analyze logs for error patterns.
        
        Args:
            logs: Log content to analyze
            
        Returns:
            List of lines containing error patterns
        """
        if not logs:
            return []
        
        error_lines = []
        lines = logs.splitlines()
        
        for line in lines:
            for pattern in self.ERROR_PATTERNS:
                if pattern.lower() in line.lower():
                    error_lines.append(line.strip())
                    break
        
        return error_lines
    
    def collect_logs_from_pods(
        self,
        pods: List[Dict[str, str]],
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Collect logs from multiple pods.
        
        Args:
            pods: List of pod dictionaries with 'name' and optional 'container'
            namespace: Namespace of the pods
            
        Returns:
            Dictionary with logs from all pods
        """
        logger.info(f"Collecting logs from {len(pods)} pods")
        
        all_logs = {}
        failed_collections = []
        
        for pod_info in pods:
            pod_name = pod_info.get("name")
            container = pod_info.get("container")
            
            if not pod_name:
                logger.warning("Pod info missing 'name' field, skipping")
                continue
            
            result = self.collect_logs(
                pod_name=pod_name,
                namespace=namespace,
                container=container
            )
            
            if result["success"]:
                all_logs[pod_name] = result
            else:
                failed_collections.append({
                    "pod_name": pod_name,
                    "error": result.get("error", "Unknown error")
                })
        
        logger.info(f"Collected logs from {len(all_logs)} pods, failed for {len(failed_collections)}")
        
        return {
            "success": True,
            "logs": all_logs,
            "failed_collections": failed_collections,
            "total_attempted": len(pods),
            "successful": len(all_logs)
        }
    
    def collect_startup_logs(
        self,
        pod_name: str,
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Collect logs focusing on startup errors.
        
        Args:
            pod_name: Name of the pod
            namespace: Namespace of the pod
            
        Returns:
            Dictionary with startup-focused logs
        """
        logger.info(f"Collecting startup logs for pod: {pod_name}")
        
        # First try current logs
        current_logs = self.collect_logs(pod_name, namespace)
        
        # If pod is restarting, also get previous logs
        previous_logs = {}
        if current_logs["success"] and current_logs["logs"]:
            # Check if logs suggest a restart
            if "restarted" in current_logs["logs"].lower() or "crash" in current_logs["logs"].lower():
                previous_logs = self.collect_logs(pod_name, namespace, previous=True)
        
        return {
            "success": True,
            "pod_name": pod_name,
            "namespace": namespace,
            "current_logs": current_logs,
            "previous_logs": previous_logs
        }
