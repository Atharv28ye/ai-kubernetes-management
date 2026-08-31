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


class NetworkInspector:
    """Inspects Kubernetes networking and services for issues."""
    
    def __init__(self, kubectl_executor: KubectlExecutor):
        """
        Initialize network inspector.
        
        Args:
            kubectl_executor: KubectlExecutor instance
        """
        self.kubectl = kubectl_executor
    
    def inspect_services(self, namespace: str = "all") -> Dict[str, Any]:
        """
        Inspect services across all or specific namespace.
        
        Args:
            namespace: Namespace to inspect ("all" for all namespaces)
            
        Returns:
            Dictionary with service health status and problematic services
        """
        logger.info(f"Inspecting services in namespace: {namespace}")
        
        # Build kubectl command
        ns_flag = "-A" if namespace == "all" else f"-n {namespace}"
        command = f"get svc {ns_flag} -o json"
        
        result = self.kubectl.execute_json(command)
        
        if not result["success"]:
            logger.error(f"Failed to get services: {result['error']}")
            return {
                "success": False,
                "error": result["error"],
                "problematic_services": []
            }
        
        services_data = result["data"]
        problematic_services = []
        
        # Process each service
        for item in services_data.get("items", []):
            service_name = item.get("metadata", {}).get("name", "unknown")
            service_namespace = item.get("metadata", {}).get("namespace", "unknown")
            
            spec = item.get("spec", {})
            service_type = spec.get("type", "ClusterIP")
            selector = spec.get("selector", {})
            ports = spec.get("ports", [])
            
            # Check for issues
            issues = []
            
            # Check if service has no selector (except for ExternalName services)
            if not selector and service_type != "ExternalName":
                issues.append("Service has no selector - endpoints won't be created automatically")
            
            # Check if service has no ports
            if not ports:
                issues.append("Service has no ports defined")
            
            # Check if selector exists but might not match any pods
            if selector:
                # We'll check endpoints later
                pass
            
            if issues:
                problematic_services.append({
                    "name": service_name,
                    "namespace": service_namespace,
                    "type": service_type,
                    "selector": selector,
                    "ports": ports,
                    "issues": issues
                })
                logger.warning(f"Found problematic service: {service_name} - {', '.join(issues)}")
        
        # Now check endpoints for services with selectors
        endpoints_issues = self._check_endpoints(namespace, services_data)
        problematic_services.extend(endpoints_issues)
        
        is_healthy = len(problematic_services) == 0
        
        logger.info(f"Service inspection complete. Healthy: {is_healthy}, Problematic services: {len(problematic_services)}")
        
        return {
            "success": True,
            "healthy": is_healthy,
            "problematic_services": problematic_services,
            "total_inspected": len(services_data.get("items", []))
        }
    
    def _check_endpoints(
        self,
        namespace: str,
        services_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Check if services have endpoints.
        
        Args:
            namespace: Namespace to check
            services_data: Services data from kubectl
            
        Returns:
            List of services with endpoint issues
        """
        endpoint_issues = []
        
        # Get all endpoints
        ns_flag = "-A" if namespace == "all" else f"-n {namespace}"
        command = f"get endpoints {ns_flag} -o json"
        result = self.kubectl.execute_json(command)
        
        if not result["success"]:
            logger.warning(f"Failed to get endpoints: {result['error']}")
            return endpoint_issues
        
        endpoints_data = result["data"]
        
        # Create a mapping of service name to endpoints
        endpoints_map = {}
        for endpoint_item in endpoints_data.get("items", []):
            endpoint_name = endpoint_item.get("metadata", {}).get("name", "")
            endpoint_namespace = endpoint_item.get("metadata", {}).get("namespace", "")
            subsets = endpoint_item.get("subsets", [])
            
            # Check if endpoints have addresses
            has_addresses = False
            for subset in subsets:
                addresses = subset.get("addresses", [])
                not_ready_addresses = subset.get("notReadyAddresses", [])
                if addresses or not_ready_addresses:
                    has_addresses = True
                    break
            
            endpoints_map[f"{endpoint_namespace}/{endpoint_name}"] = has_addresses
        
        # Check each service
        for service_item in services_data.get("items", []):
            service_name = service_item.get("metadata", {}).get("name", "")
            service_namespace = service_item.get("metadata", {}).get("namespace", "")
            selector = service_item.get("spec", {}).get("selector", {})
            service_type = service_item.get("spec", {}).get("type", "ClusterIP")
            
            # Skip services without selectors or ExternalName services
            if not selector or service_type == "ExternalName":
                continue
            
            service_key = f"{service_namespace}/{service_name}"
            has_endpoints = endpoints_map.get(service_key, False)
            
            if not has_endpoints:
                endpoint_issues.append({
                    "name": service_name,
                    "namespace": service_namespace,
                    "type": service_type,
                    "selector": selector,
                    "issues": ["Service has no endpoints - selector may not match any pods"]
                })
                logger.warning(f"Service {service_name} has no endpoints")
        
        return endpoint_issues
    
    def check_dns_resolution(self, namespace: str = "default") -> Dict[str, Any]:
        """
        Check DNS resolution by testing CoreDNS pods.
        
        Args:
            namespace: Namespace to check (usually kube-system)
            
        Returns:
            Dictionary with DNS health status
        """
        logger.info(f"Checking DNS resolution in namespace: {namespace}")
        
        # Check CoreDNS pods
        command = f"get pods -n kube-system -l k8s-app=kube-dns -o json"
        result = self.kubectl.execute_json(command)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result["error"],
                "dns_healthy": False
            }
        
        pods_data = result["data"]
        coredns_pods = pods_data.get("items", [])
        
        issues = []
        
        for pod in coredns_pods:
            pod_name = pod.get("metadata", {}).get("name", "")
            pod_phase = pod.get("status", {}).get("phase", "")
            
            if pod_phase != "Running":
                issues.append(f"CoreDNS pod {pod_name} is {pod_phase}")
        
        # Check if CoreDNS service exists
        svc_command = "get svc kube-dns -n kube-system -o json"
        svc_result = self.kubectl.execute_json(svc_command)
        
        if not svc_result["success"]:
            issues.append("CoreDNS service not found or inaccessible")
        
        is_healthy = len(issues) == 0
        
        logger.info(f"DNS check complete. Healthy: {is_healthy}, Issues: {len(issues)}")
        
        return {
            "success": True,
            "dns_healthy": is_healthy,
            "coredns_pods_count": len(coredns_pods),
            "issues": issues
        }
    
    def check_network_policies(self, namespace: str = "all") -> Dict[str, Any]:
        """
        Check for network policies that might block traffic.
        
        Args:
            namespace: Namespace to check ("all" for all namespaces)
            
        Returns:
            Dictionary with network policy information
        """
        logger.info(f"Checking network policies in namespace: {namespace}")
        
        ns_flag = "-A" if namespace == "all" else f"-n {namespace}"
        command = f"get networkpolicies {ns_flag} -o json"
        
        result = self.kubectl.execute_json(command)
        
        if not result["success"]:
            return {
                "success": False,
                "error": result["error"],
                "network_policies": []
            }
        
        policies_data = result["data"]
        policies = []
        
        for item in policies_data.get("items", []):
            policy_name = item.get("metadata", {}).get("name", "")
            policy_namespace = item.get("metadata", {}).get("namespace", "")
            spec = item.get("spec", {})
            
            pod_selector = spec.get("podSelector", {})
            policy_types = spec.get("policyTypes", [])
            
            policies.append({
                "name": policy_name,
                "namespace": policy_namespace,
                "pod_selector": pod_selector,
                "policy_types": policy_types
            })
        
        logger.info(f"Found {len(policies)} network policies")
        
        return {
            "success": True,
            "network_policies": policies,
            "total_policies": len(policies)
        }
    
    def get_service_details(
        self,
        service_name: str,
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific service.
        
        Args:
            service_name: Name of the service
            namespace: Namespace of the service
            
        Returns:
            Dictionary with service details
        """
        command = f"get svc {service_name} -n {namespace} -o json"
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
