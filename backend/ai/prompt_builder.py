from typing import Dict, Any
from loguru import logger


class PromptBuilder:
    """Builds structured prompts for Kubernetes troubleshooting AI."""
    
    SYSTEM_PROMPT = """You are a Senior Kubernetes Site Reliability Engineer (SRE) with deep expertise in troubleshooting Kubernetes clusters. 

Your task is to analyze Kubernetes investigation data and provide:
1. Root Cause Analysis
2. Detailed Explanation
3. Actionable Fix Recommendations
4. Specific kubectl Commands
5. Prevention Recommendations
6. Confidence Score (0-100%)

Follow these guidelines:
- Be specific and practical
- Focus on Kubernetes-specific solutions
- Provide exact kubectl commands when possible
- Consider the correlation between pods, logs, events, deployments, and networking
- Avoid generic advice
- Explain your reasoning clearly
- Base confidence on evidence strength and clarity

IMPORTANT OUTPUT RULES:
Return ONLY valid JSON.
Do NOT use markdown.
Do NOT wrap the JSON in ```json code fences.
Use exactly this structure:
{
  "root_cause": "short root cause",
  "explanation": "short explanation",
  "fix": [
    "fix 1",
    "fix 2",
    "fix 3"
  ],
  "kubectl_commands": [
    "command 1",
    "command 2",
    "command 3"
  ],
  "prevention": [
    "prevention 1",
    "prevention 2"
  ],
  "confidence": 85,
  "confidence_reasoning": "short reason"
}
Rules:
- Keep root_cause under 50 words.
- Keep explanation under 100 words.
- Maximum 3 fixes.
- Maximum 3 kubectl commands.
- Maximum 2 prevention recommendations.
- confidence must be an integer from 0 to 100.
- Return ONLY JSON.
IMPORTANT DIAGNOSTIC RULES:
- Base the root cause primarily on concrete Kubernetes events,
  pod states, deployment states, and actual errors.
- Do NOT assume that a Service without a selector is broken.
- The default Kubernetes "kubernetes" Service may intentionally
  have manually managed endpoints.
- Do not claim causation unless the investigation data supports it.
- Distinguish symptoms from root causes.
- Prefer concrete errors such as FailedMount, BackOff,
  CrashLoopBackOff, FailedScheduling, ImagePullBackOff,
  readiness failures, and configuration errors.
- If multiple problems exist, identify the most likely primary
  root cause and list the others as contributing symptoms.
"""
    
    def __init__(self):
        """Initialize prompt builder."""
        self.system_prompt = self.SYSTEM_PROMPT
    
    def build_investigation_prompt(self, investigation_data: Dict[str, Any]) -> str:
        """
        Build a structured prompt from investigation data.
        
        Args:
            investigation_data: Dictionary containing pods, logs, events, deployments, network data
            
        Returns:
            Structured prompt string for LLM
        """
        logger.info("Building investigation prompt")
        
        prompt_parts = [
            "KUBERNETES INVESTIGATION DATA",
            "=" * 50
        ]
        
        # Add pod information
        pods_data = investigation_data.get("pods", {})
        prompt_parts.append(self._format_pods_section(pods_data))
        
        # Add logs information
        logs_data = investigation_data.get("logs", {})
        prompt_parts.append(self._format_logs_section(logs_data))
        
        # Add events information
        events_data = investigation_data.get("events", {})
        prompt_parts.append(self._format_events_section(events_data))
        
        # Add deployment information
        deployments_data = investigation_data.get("deployments", {})
        prompt_parts.append(self._format_deployments_section(deployments_data))
        
        # Add network information
        network_data = investigation_data.get("network", {})
        prompt_parts.append(self._format_network_section(network_data))
        
        # Add analysis request
        prompt_parts.extend([
            "=" * 50,
            "ANALYSIS REQUEST",
            "Based on the investigation data above, analyze the Kubernetes issues and provide:",
            "1. Root cause of the problem",
            "2. Detailed explanation of what happened",
            "3. Specific fix recommendations",
            "4. Exact kubectl commands to resolve the issue",
            "5. Prevention recommendations",
            "6. Confidence score (0-100%) with reasoning",
            "",
            "Return your response in the specified JSON format."
        ])
        
        full_prompt = "\n\n".join(prompt_parts)
        logger.info(f"Built investigation prompt with {len(full_prompt)} characters")
        
        return full_prompt
    
    def _format_pods_section(self, pods_data: Dict[str, Any]) -> str:
        """Format pods section of the prompt."""
        section = ["POD STATUS", "-" * 20]
        
        if pods_data.get("healthy"):
            section.append("Status: All pods are healthy")
        else:
            section.append(f"Status: Unhealthy - {len(pods_data.get('problematic_pods', []))} problematic pods")
            
            for pod in pods_data.get("problematic_pods", []):
                section.append(f"  - Pod: {pod.get('name')} in namespace {pod.get('namespace')}")
                section.append(f"    Status: {pod.get('status')}")
                section.append(f"    Phase: {pod.get('phase')}")
        
        if pods_data.get("error"):
            section.append(f"Error: {pods_data.get('error')}")
        
        return "\n".join(section)
    
    def _format_logs_section(self, logs_data: Dict[str, Any]) -> str:
        """Format logs section of the prompt."""
        section = ["LOGS ANALYSIS", "-" * 20]
        
        if logs_data.get("success"):
            logs = logs_data.get("logs", {})
            section.append(f"Logs collected from {len(logs)} pods")
            
            for pod_name, pod_logs in logs.items():
                section.append(f"  - Pod: {pod_name}")
                section.append(f"    Error count: {pod_logs.get('error_count', 0)}")
                
                if pod_logs.get("errors_found"):
                    section.append("    Key errors:")
                    for error in pod_logs.get("errors_found", [])[:5]:  # Limit to top 5
                        section.append(f"      * {error[:100]}...")  # Truncate long errors
                
                if pod_logs.get("logs"):
                    # Include a sample of the logs
                    log_sample = pod_logs.get("logs", "")[:500]
                    section.append(f"    Sample logs: {log_sample}...")
        else:
            section.append(f"Log collection failed: {logs_data.get('error', 'Unknown error')}")
            section.append(f"Message: {logs_data.get('message', '')}")
        
        return "\n".join(section)
    
    def _format_events_section(self, events_data: Dict[str, Any]) -> str:
        """Format events section of the prompt."""
        section = ["EVENTS ANALYSIS", "-" * 20]
        
        if events_data.get("success"):
            section.append(f"Total events analyzed: {events_data.get('total_events_analyzed', 0)}")
            section.append(f"Problematic events found: {len(events_data.get('problematic_events', []))}")
            
            # Show event summary
            event_summary = events_data.get("event_summary", {})
            if event_summary:
                section.append("Event summary by type:")
                for event_type, count in event_summary.items():
                    section.append(f"  - {event_type}: {count} occurrences")
            
            # Show recent problematic events
            problematic_events = events_data.get("problematic_events", [])[:10]  # Limit to 10
            if problematic_events:
                section.append("Recent problematic events:")
                for event in problematic_events:
                    section.append(f"  - {event.get('type')}: {event.get('reason')}")
                    section.append(f"    Resource: {event.get('involved_object', {}).get('kind')}/{event.get('involved_object', {}).get('name')}")
                    section.append(f"    Message: {event.get('message', '')[:100]}...")
        else:
            section.append(f"Event analysis failed: {events_data.get('error', 'Unknown error')}")
        
        return "\n".join(section)
    
    def _format_deployments_section(self, deployments_data: Dict[str, Any]) -> str:
        """Format deployments section of the prompt."""
        section = ["DEPLOYMENT STATUS", "-" * 20]
        
        if deployments_data.get("success"):
            if deployments_data.get("healthy"):
                section.append("Status: All deployments are healthy")
            else:
                section.append(f"Status: Unhealthy - {len(deployments_data.get('problematic_deployments', []))} problematic deployments")
                
                for deployment in deployments_data.get("problematic_deployments", []):
                    section.append(f"  - Deployment: {deployment.get('name')} in namespace {deployment.get('namespace')}")
                    section.append(f"    Replicas: {deployment.get('available_replicas')}/{deployment.get('replicas')} available")
                    section.append(f"    Issues: {', '.join(deployment.get('issues', []))}")
        else:
            section.append(f"Deployment analysis failed: {deployments_data.get('error', 'Unknown error')}")
        
        return "\n".join(section)
    
    def _format_network_section(self, network_data: Dict[str, Any]) -> str:
        """Format network section of the prompt."""
        section = ["NETWORK STATUS", "-" * 20]
        
        if network_data.get("success"):
            if network_data.get("healthy"):
                section.append("Status: All services are healthy")
            else:
                section.append(f"Status: Issues found - {len(network_data.get('problematic_services', []))} problematic services")
                
                for service in network_data.get("problematic_services", []):
                    section.append(f"  - Service: {service.get('name')} in namespace {service.get('namespace')}")
                    section.append(f"    Type: {service.get('type')}")
                    section.append(f"    Issues: {', '.join(service.get('issues', []))}")
            
            # Add DNS status
            dns_data = network_data.get("dns", {})
            if dns_data:
                dns_healthy = dns_data.get("dns_healthy", False)
                section.append(f"DNS Status: {'Healthy' if dns_healthy else 'Unhealthy'}")
                if dns_data.get("issues"):
                    section.append(f"DNS Issues: {', '.join(dns_data.get('issues', []))}")
        else:
            section.append(f"Network analysis failed: {network_data.get('error', 'Unknown error')}")
        
        return "\n".join(section)
    
    def build_targeted_prompt(self, resource_name: str, resource_type: str, investigation_data: Dict[str, Any]) -> str:
        """
        Build a prompt for targeted resource investigation.
        
        Args:
            resource_name: Name of the resource
            resource_type: Type of resource (pod, deployment, service)
            investigation_data: Investigation data for the specific resource
            
        Returns:
            Structured prompt string for LLM
        """
        logger.info(f"Building targeted prompt for {resource_type}/{resource_name}")
        
        prompt_parts = [
            f"TARGETED INVESTIGATION: {resource_type.upper()}/{resource_name}",
            "=" * 50,
            "Analyze this specific Kubernetes resource and provide:",
            "1. Root cause of the problem",
            "2. Detailed explanation",
            "3. Specific fix recommendations",
            "4. Exact kubectl commands",
            "5. Prevention recommendations",
            "6. Confidence score with reasoning",
            "",
            "INVESTIGATION DATA:",
            str(investigation_data),
            "",
            "Return your response in the specified JSON format."
        ]
        
        return "\n\n".join(prompt_parts)