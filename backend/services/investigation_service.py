from typing import Dict, Any, Optional
from loguru import logger
import os
import sys
import time

# Add backend directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    from kubectl.kubectl_executor import KubectlExecutor
    from kubernetes.pod_inspector import PodInspector
    from kubernetes.logs_collector import LogsCollector
    from kubernetes.events_analyzer import EventsAnalyzer
    from kubernetes.deployment_inspector import DeploymentInspector
    from kubernetes.network_inspector import NetworkInspector
    from ai.ai_agent import AIAgent
    from services.realtime_service import RealtimeService
except ImportError as e:
    logger.error(f"Failed to import kubernetes modules: {e}")
    raise


class InvestigationService:
    """Orchestrates Kubernetes investigation components."""
    
    def __init__(self, kubeconfig_path: Optional[str] = None, enable_ai: bool = True):
        """
        Initialize investigation service.
        
        Args:
            kubeconfig_path: Optional path to kubeconfig file
            enable_ai: Whether to enable AI analysis
        """
        self.kubeconfig_path = kubeconfig_path or os.getenv("KUBECONFIG_PATH")
        self.enable_ai = enable_ai
        self.kubectl_timeout = int(os.getenv("KUBECTL_TIMEOUT", "90"))
        
        # Initialize kubectl executor with increased timeout for cluster-wide queries
        self.kubectl = KubectlExecutor(kubeconfig_path=self.kubeconfig_path, timeout=self.kubectl_timeout)
        
        # Initialize all inspectors with increased timeout
        self.pod_inspector = PodInspector(self.kubectl)
        self.logs_collector = LogsCollector(self.kubectl)
        self.events_analyzer = EventsAnalyzer(self.kubectl)
        self.deployment_inspector = DeploymentInspector(self.kubectl)
        self.network_inspector = NetworkInspector(self.kubectl)
        
        # Initialize AI agent
        self.ai_agent = AIAgent() if enable_ai else None
        
        # Initialize realtime service
        self.realtime = RealtimeService()
        
        logger.info(f"Investigation service initialized (AI enabled: {enable_ai})")
    
    async def investigate(
        self,
        namespace: str = "all",
        collect_logs: bool = True,
        max_log_lines: int = 100
    ) -> Dict[str, Any]:
        """
        Run full Kubernetes investigation.
        
        Args:
            namespace: Namespace to investigate ("all" for all namespaces)
            collect_logs: Whether to collect logs from problematic pods
            max_log_lines: Maximum number of log lines to collect per pod
            
        Returns:
            Dictionary with complete investigation results
        """
        logger.info(f"Starting Kubernetes investigation for namespace: {namespace}")
        
        investigation_result = {
            "status": "success",
            "namespace": namespace,
            "investigation": {
                "pods": {},
                "logs": {},
                "events": {},
                "deployments": {},
                "network": {}
            }
        }
        
        try:
            # Generate investigation ID for realtime updates
            investigation_id = f"inv_{int(time.time())}"
            investigation_result["investigation_id"] = investigation_id
            
            # Step 1: Check Pods
            logger.info("Step 1: Inspecting pods")
            if self.realtime.is_enabled():
                await self.realtime.broadcast_progress(investigation_id, "✓ Checking Pods")
            pods_result = self.pod_inspector.inspect_pods(namespace)
            
            # Check for cluster connection errors
            if not pods_result.get("success") and "friendly_error" in pods_result:
                investigation_result["status"] = "error"
                investigation_result["error"] = pods_result["friendly_error"]
                investigation_result["investigation"]["pods"] = pods_result
                return investigation_result
                
            investigation_result["investigation"]["pods"] = pods_result
            
            # Step 2: Collect Logs (if there are problematic pods and collection is enabled)
            if collect_logs and pods_result.get("problematic_pods"):
                logger.info("Step 2: Collecting logs from problematic pods")
                if self.realtime.is_enabled():
                    await self.realtime.broadcast_progress(investigation_id, "✓ Reading Logs")
                problematic_pods = pods_result.get("problematic_pods", [])
                
                # Update logs collector max lines if specified
                original_max_lines = self.logs_collector.max_lines
                self.logs_collector.max_lines = max_log_lines
                
                try:
                    logs_result = self.logs_collector.collect_logs_from_pods(
                        pods=[{"name": pod["name"], "namespace": pod["namespace"]} 
                              for pod in problematic_pods],
                        namespace=namespace if namespace != "all" else "default"
                    )
                    investigation_result["investigation"]["logs"] = logs_result
                except Exception as e:
                    logger.error(f"Failed to collect logs: {str(e)}")
                    investigation_result["investigation"]["logs"] = {
                        "success": False,
                        "error": str(e),
                        "message": "Failed to collect logs from problematic pods"
                    }
                finally:
                    # Restore original max lines
                    self.logs_collector.max_lines = original_max_lines
            else:
                logger.info("Step 2: Skipping log collection (no problematic pods or disabled)")
                investigation_result["investigation"]["logs"] = {
                    "success": True,
                    "message": "Log collection skipped - no problematic pods or disabled",
                    "logs": {}
                }
            
            # Step 3: Analyze Events
            logger.info("Step 3: Analyzing events")
            if self.realtime.is_enabled():
                await self.realtime.broadcast_progress(investigation_id, "✓ Analyzing Events")
            try:
                events_result = self.events_analyzer.analyze_events(namespace)
                investigation_result["investigation"]["events"] = events_result
            except Exception as e:
                logger.error(f"Failed to analyze events: {str(e)}")
                investigation_result["investigation"]["events"] = {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to analyze Kubernetes events"
                }
            
            # Step 4: Inspect Deployments
            logger.info("Step 4: Inspecting deployments")
            if self.realtime.is_enabled():
                await self.realtime.broadcast_progress(investigation_id, "✓ Inspecting Deployments")
            try:
                deployments_result = self.deployment_inspector.inspect_deployments(namespace)
                investigation_result["investigation"]["deployments"] = deployments_result
            except Exception as e:
                logger.error(f"Failed to inspect deployments: {str(e)}")
                investigation_result["investigation"]["deployments"] = {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to inspect Kubernetes deployments"
                }
            
            # Step 5: Check Networking
            logger.info("Step 5: Inspecting networking")
            if self.realtime.is_enabled():
                await self.realtime.broadcast_progress(investigation_id, "✓ Checking Networking")
            try:
                network_result = self.network_inspector.inspect_services(namespace)
                investigation_result["investigation"]["network"] = network_result
            except Exception as e:
                logger.error(f"Failed to inspect networking: {str(e)}")
                investigation_result["investigation"]["network"] = {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to inspect Kubernetes networking"
                }
            
            # Also check DNS
            try:
                dns_result = self.network_inspector.check_dns_resolution()
                investigation_result["investigation"]["network"]["dns"] = dns_result
            except Exception as e:
                logger.error(f"Failed to check DNS: {str(e)}")
                investigation_result["investigation"]["network"]["dns"] = {
                    "success": False,
                    "error": str(e),
                    "message": "Failed to check DNS resolution"
                }
            
            logger.info("Kubernetes investigation completed successfully")
            
            # Step 6: AI Analysis (if enabled)
            if self.ai_agent and investigation_result["status"] == "success":
                logger.info("Step 6: Running AI analysis")
                if self.realtime.is_enabled():
                    await self.realtime.broadcast_progress(investigation_id, "✓ AI Reasoning")
                try:
                    diagnosis = self.ai_agent.analyze_investigation(
                        investigation_result["investigation"],
                        enable_ai=self.enable_ai
                    )
                    investigation_result["diagnosis"] = diagnosis
                    if self.realtime.is_enabled():
                        await self.realtime.broadcast_progress(investigation_id, "✓ Root Cause Found")
                    logger.info("AI analysis completed successfully")
                except Exception as e:
                    logger.error(f"AI analysis failed: {str(e)}")
                    investigation_result["diagnosis"] = {
                        "error": f"AI analysis failed: {str(e)}",
                        "ai_generated": False
                    }
            else:
                logger.info("Step 6: Skipping AI analysis (disabled or investigation failed)")
                investigation_result["diagnosis"] = None
            
        except Exception as e:
            logger.error(f"Error during investigation: {str(e)}")
            investigation_result["status"] = "error"
            investigation_result["error"] = str(e)
            investigation_result["diagnosis"] = None
        
        return investigation_result
    
    def quick_investigation(self, namespace: str = "default") -> Dict[str, Any]:
        """
        Run a quick investigation focusing on critical issues only.
        
        Args:
            namespace: Namespace to investigate
            
        Returns:
            Dictionary with quick investigation results
        """
        logger.info(f"Starting quick investigation for namespace: {namespace}")
        
        return self.investigate(
            namespace=namespace,
            collect_logs=False,
            max_log_lines=50
        )
    
    def targeted_investigation(
        self,
        resource_name: str,
        resource_type: str = "pod",
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Run investigation on a specific resource.
        
        Args:
            resource_name: Name of the resource
            resource_type: Type of resource (pod, deployment, service)
            namespace: Namespace of the resource
            
        Returns:
            Dictionary with targeted investigation results
        """
        logger.info(f"Starting targeted investigation for {resource_type}/{resource_name} in {namespace}")
        
        result = {
            "status": "success",
            "resource_name": resource_name,
            "resource_type": resource_type,
            "namespace": namespace,
            "investigation": {}
        }
        
        try:
            if resource_type == "pod":
                # Get pod details
                pod_details = self.pod_inspector.get_pod_details(resource_name, namespace)
                result["investigation"]["pod_details"] = pod_details
                
                # Get pod events
                pod_events = self.events_analyzer.get_events_for_resource(
                    resource_name, "Pod", namespace
                )
                result["investigation"]["events"] = pod_events
                
                # Collect logs
                logs = self.logs_collector.collect_logs(resource_name, namespace)
                result["investigation"]["logs"] = logs
                
            elif resource_type == "deployment":
                # Get deployment details
                deployment_details = self.deployment_inspector.get_deployment_details(
                    resource_name, namespace
                )
                result["investigation"]["deployment_details"] = deployment_details
                
                # Check replicas
                replica_status = self.deployment_inspector.check_deployment_replicas(
                    resource_name, namespace
                )
                result["investigation"]["replica_status"] = replica_status
                
                # Get deployment events
                deployment_events = self.events_analyzer.get_events_for_resource(
                    resource_name, "Deployment", namespace
                )
                result["investigation"]["events"] = deployment_events
                
            elif resource_type == "service":
                # Get service details
                service_details = self.network_inspector.get_service_details(
                    resource_name, namespace
                )
                result["investigation"]["service_details"] = service_details
                
                # Get service events
                service_events = self.events_analyzer.get_events_for_resource(
                    resource_name, "Service", namespace
                )
                result["investigation"]["events"] = service_events
                
            else:
                result["status"] = "error"
                result["error"] = f"Unsupported resource type: {resource_type}"
            
            # Add AI analysis if enabled and investigation was successful
            if self.ai_agent and result["status"] == "success":
                try:
                    diagnosis = self.ai_agent.analyze_targeted_investigation(
                        resource_name=resource_name,
                        resource_type=resource_type,
                        investigation_data=result["investigation"],
                        enable_ai=self.enable_ai
                    )
                    result["diagnosis"] = diagnosis
                    logger.info("Targeted AI analysis completed successfully")
                except Exception as e:
                    logger.error(f"Targeted AI analysis failed: {str(e)}")
                    result["diagnosis"] = {
                        "error": f"AI analysis failed: {str(e)}",
                        "ai_generated": False
                    }
            else:
                result["diagnosis"] = None
                
        except Exception as e:
            logger.error(f"Error during targeted investigation: {str(e)}")
            result["status"] = "error"
            result["error"] = str(e)
            result["diagnosis"] = None
        
        return result
