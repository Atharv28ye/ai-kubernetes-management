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


class DeploymentInspector:
    """Inspects Kubernetes deployments for health issues."""
    
    def __init__(self, kubectl_executor: KubectlExecutor):
        """
        Initialize deployment inspector.
        
        Args:
            kubectl_executor: KubectlExecutor instance
        """
        self.kubectl = kubectl_executor
    
    def inspect_deployments(self, namespace: str = "all") -> Dict[str, Any]:
        """
        Inspect deployments across all or specific namespace.
        
        Args:
            namespace: Namespace to inspect ("all" for all namespaces)
            
        Returns:
            Dictionary with deployment health status and problematic deployments
        """
        logger.info(f"Inspecting deployments in namespace: {namespace}")
        
        # Build kubectl command
        ns_flag = "-A" if namespace == "all" else f"-n {namespace}"
        command = f"get deployments {ns_flag} -o json"
        
        result = self.kubectl.execute_json(command)
        
        if not result["success"]:
            logger.error(f"Failed to get deployments: {result['error']}")
            return {
                "success": False,
                "error": result["error"],
                "problematic_deployments": []
            }
        
        deployments_data = result["data"]
        problematic_deployments = []
        
        # Process each deployment
        for item in deployments_data.get("items", []):
            deployment_name = item.get("metadata", {}).get("name", "unknown")
            deployment_namespace = item.get("metadata", {}).get("namespace", "unknown")
            
            # Get deployment status
            spec = item.get("spec", {})
            status = item.get("status", {})
            
            replicas = spec.get("replicas", 0)
            available_replicas = status.get("availableReplicas", 0)
            unavailable_replicas = status.get("unavailableReplicas", 0)
            updated_replicas = status.get("updatedReplicas", 0)
            
            # Check for issues
            issues = []
            
            # Check if replicas are unavailable
            if unavailable_replicas > 0:
                issues.append(f"{unavailable_replicas} unavailable replicas")
            
            # Check if available replicas don't match desired replicas
            if available_replicas < replicas:
                issues.append(f"Only {available_replicas}/{replicas} replicas available")
            
            # Check if rollout is in progress
            if updated_replicas < replicas:
                issues.append(f"Rollout in progress: {updated_replicas}/{replicas} updated")
            
            # Check deployment conditions
            conditions = status.get("conditions", [])
            for condition in conditions:
                condition_type = condition.get("type", "")
                condition_status = condition.get("status", "")
                reason = condition.get("reason", "")
                message = condition.get("message", "")
                
                if condition_type == "Available" and condition_status != "True":
                    issues.append(f"Deployment not available: {reason}")
                
                if condition_type == "Progressing" and condition_status != "True":
                    issues.append(f"Deployment not progressing: {reason}")
                
                if condition_type == "ReplicaFailure" and condition_status == "True":
                    issues.append(f"Replica failure: {message}")
            
            if issues:
                problematic_deployments.append({
                    "name": deployment_name,
                    "namespace": deployment_namespace,
                    "replicas": replicas,
                    "available_replicas": available_replicas,
                    "unavailable_replicas": unavailable_replicas,
                    "updated_replicas": updated_replicas,
                    "issues": issues,
                    "conditions": conditions
                })
                logger.warning(f"Found problematic deployment: {deployment_name} - {', '.join(issues)}")
        
        is_healthy = len(problematic_deployments) == 0
        
        logger.info(f"Deployment inspection complete. Healthy: {is_healthy}, Problematic deployments: {len(problematic_deployments)}")
        
        return {
            "success": True,
            "healthy": is_healthy,
            "problematic_deployments": problematic_deployments,
            "total_inspected": len(deployments_data.get("items", []))
        }
    
    def get_deployment_details(
        self,
        deployment_name: str,
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific deployment.
        
        Args:
            deployment_name: Name of the deployment
            namespace: Namespace of the deployment
            
        Returns:
            Dictionary with deployment details
        """
        command = f"get deployment {deployment_name} -n {namespace} -o json"
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
    
    def get_deployment_rollout_status(
        self,
        deployment_name: str,
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Get rollout status for a specific deployment.
        
        Args:
            deployment_name: Name of the deployment
            namespace: Namespace of the deployment
            
        Returns:
            Dictionary with rollout status
        """
        command = f"rollout status deployment/{deployment_name} -n {namespace}"
        result = self.kubectl.execute(command)
        
        return {
            "success": result["success"],
            "deployment_name": deployment_name,
            "namespace": namespace,
            "output": result["stdout"],
            "error": result["stderr"] if not result["success"] else None
        }
    
    def check_deployment_replicas(
        self,
        deployment_name: str,
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Check if deployment has the correct number of replicas.
        
        Args:
            deployment_name: Name of the deployment
            namespace: Namespace of the deployment
            
        Returns:
            Dictionary with replica status
        """
        details = self.get_deployment_details(deployment_name, namespace)
        
        if not details["success"]:
            return details
        
        data = details["data"]
        spec = data.get("spec", {})
        status = data.get("status", {})
        
        replicas = spec.get("replicas", 0)
        available_replicas = status.get("availableReplicas", 0)
        ready_replicas = status.get("readyReplicas", 0)
        
        is_healthy = available_replicas == replicas and ready_replicas == replicas
        
        return {
            "success": True,
            "deployment_name": deployment_name,
            "namespace": namespace,
            "healthy": is_healthy,
            "desired_replicas": replicas,
            "available_replicas": available_replicas,
            "ready_replicas": ready_replicas,
            "issues": [] if is_healthy else [
                f"Expected {replicas} replicas, got {available_replicas} available"
            ]
        }
