from typing import Dict, Any, Optional
from loguru import logger
import os
import sys

# Add backend directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(current_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    from ai.prompt_builder import PromptBuilder
    from ai.llm_client import LLMClient
except ImportError:
    from .prompt_builder import PromptBuilder
    from .llm_client import LLMClient


class AIAgent:
    """AI Kubernetes Agent that orchestrates LLM-based analysis."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        """
        Initialize AI Agent.

        Args:
            api_key: OpenRouter API key
            model: Model name
        """
        self.prompt_builder = PromptBuilder()
        self.llm_client = LLMClient(api_key=api_key, model=model)

        logger.info("AI Kubernetes Agent initialized")

    def analyze_investigation(
        self,
        investigation_data: Dict[str, Any],
        enable_ai: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze Kubernetes investigation data and generate diagnosis.

        Args:
            investigation_data: Dictionary containing pods, logs, events, deployments, network data
            enable_ai: Whether to use AI analysis (if False, returns basic analysis)

        Returns:
            Dictionary with root cause analysis and recommendations
        """
        logger.info("Starting AI analysis of investigation data")

        if not enable_ai:
            logger.info("AI analysis disabled, returning basic analysis")
            return self._basic_analysis(investigation_data)

        # Check if LLM client is configured
        health = self.llm_client.health_check()
        if not health.get("configured"):
            logger.warning("LLM client not configured, falling back to basic analysis")
            return self._basic_analysis(investigation_data)

        try:
            # Build the investigation prompt
            system_prompt = self.prompt_builder.system_prompt
            user_prompt = self.prompt_builder.build_investigation_prompt(investigation_data)

            # Get LLM completion
            llm_response = self.llm_client.generate_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=2000
            )

            if not llm_response["success"]:
                logger.error(f"LLM request failed: {llm_response['error']}")
                return self._basic_analysis(investigation_data)

            # Extract the analysis from LLM response
            ai_analysis = llm_response["content"]

            # Validate and structure the response
            diagnosis = self._structure_diagnosis(ai_analysis, investigation_data)

            logger.info("AI analysis completed successfully")
            return diagnosis

        except Exception as e:
            logger.error(f"AI analysis failed: {str(e)}")
            return self._basic_analysis(investigation_data)

    def analyze_targeted_investigation(
        self,
        resource_name: str,
        resource_type: str,
        investigation_data: Dict[str, Any],
        enable_ai: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze targeted resource investigation data.

        Args:
            resource_name: Name of the resource
            resource_type: Type of resource (pod, deployment, service)
            investigation_data: Investigation data for the specific resource
            enable_ai: Whether to use AI analysis

        Returns:
            Dictionary with analysis and recommendations
        """
        logger.info(f"Starting AI analysis for {resource_type}/{resource_name}")

        if not enable_ai:
            return self._basic_targeted_analysis(resource_name, resource_type, investigation_data)

        health = self.llm_client.health_check()
        if not health.get("configured"):
            logger.warning("LLM client not configured, falling back to basic analysis")
            return self._basic_targeted_analysis(resource_name, resource_type, investigation_data)

        try:
            system_prompt = self.prompt_builder.system_prompt
            user_prompt = self.prompt_builder.build_targeted_prompt(
                resource_name, resource_type, investigation_data
            )

            llm_response = self.llm_client.generate_completion(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=0.7,
                max_tokens=2000
            )

            if not llm_response["success"]:
                logger.error(f"LLM request failed: {llm_response['error']}")
                return self._basic_targeted_analysis(resource_name, resource_type, investigation_data)

            ai_analysis = llm_response["content"]
            diagnosis = self._structure_diagnosis(ai_analysis, investigation_data)

            # Add resource context
            diagnosis["resource_name"] = resource_name
            diagnosis["resource_type"] = resource_type

            return diagnosis

        except Exception as e:
            logger.error(f"Targeted AI analysis failed: {str(e)}")
            return self._basic_targeted_analysis(resource_name, resource_type, investigation_data)

    def _structure_diagnosis(
        self,
        ai_analysis: Dict[str, Any],
        investigation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Structure and validate the AI diagnosis.

        Args:
            ai_analysis: Raw analysis from LLM
            investigation_data: Original investigation data

        Returns:
            Structured diagnosis dictionary
        """
        if not isinstance(ai_analysis, dict):
            ai_analysis = {}

        # Support alternative field names returned by some models
        root_cause = (
            ai_analysis.get("root_cause")
            or ai_analysis.get("rootCause")
            or ai_analysis.get("cause")
            or ai_analysis.get("diagnosis")
            or "Unable to determine root cause"
        )
        explanation = (
            ai_analysis.get("explanation")
            or ai_analysis.get("reason")
            or ai_analysis.get("details")
            or "No explanation provided"
        )
        fix = (
            ai_analysis.get("fix")
            or ai_analysis.get("suggested_fix")
            or ai_analysis.get("recommendation")
            or ai_analysis.get("recommendations")
            or "No fix recommendation provided"
        )
        kubectl_commands = (
            ai_analysis.get("kubectl_commands")
            or ai_analysis.get("commands")
            or []
        )
        prevention = (
            ai_analysis.get("prevention")
            or ai_analysis.get("prevention_recommendations")
            or "No prevention recommendations provided"
        )
        confidence = (
            ai_analysis.get("confidence")
            or ai_analysis.get("confidence_score")
            or 50
        )
        confidence_reasoning = (
            ai_analysis.get("confidence_reasoning")
            or ai_analysis.get("reasoning")
            or "No confidence reasoning provided"
        )

        diagnosis = {
            "root_cause": root_cause,
            "explanation": explanation,
            "fix": fix,
            "kubectl_commands": kubectl_commands,
            "prevention": prevention,
            "confidence": confidence,
            "confidence_reasoning": confidence_reasoning,
            "ai_generated": True,
            "investigation_summary": self._create_investigation_summary(
                investigation_data
            )
        }

        # Validate confidence score
        try:
            confidence = int(diagnosis["confidence"])
            # Handle models returning 0.85 instead of 85
            if 0 < confidence <= 1:
                confidence = int(confidence * 100)
            diagnosis["confidence"] = max(0, min(100, confidence))  # Clamp between 0-100
        except (ValueError, TypeError):
            diagnosis["confidence"] = 50

        # Ensure kubectl_commands is a list
        if not isinstance(diagnosis["kubectl_commands"], list):
            diagnosis["kubectl_commands"] = [str(diagnosis["kubectl_commands"])]

        # Convert lists to readable strings where needed
        if isinstance(diagnosis["fix"], list):
            diagnosis["fix"] = "\n".join(
                f"{i + 1}. {item}" for i, item in enumerate(diagnosis["fix"])
            )
        if isinstance(diagnosis["prevention"], list):
            diagnosis["prevention"] = "\n".join(
                f"- {item}" for item in diagnosis["prevention"]
            )

        return diagnosis

    def _create_investigation_summary(self, investigation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a summary of the investigation data.

        Args:
            investigation_data: Full investigation data

        Returns:
            Summary dictionary
        """
        summary = {
            "pods_healthy": investigation_data.get("pods", {}).get("healthy", True),
            "problematic_pods_count": len(investigation_data.get("pods", {}).get("problematic_pods", [])),
            "events_analyzed": investigation_data.get("events", {}).get("total_events_analyzed", 0),
            "problematic_events_count": len(investigation_data.get("events", {}).get("problematic_events", [])),
            "deployments_healthy": investigation_data.get("deployments", {}).get("healthy", True),
            "problematic_deployments_count": len(investigation_data.get("deployments", {}).get("problematic_deployments", [])),
            "network_healthy": investigation_data.get("network", {}).get("healthy", True),
            "problematic_services_count": len(investigation_data.get("network", {}).get("problematic_services", []))
        }

        return summary

    def _basic_analysis(self, investigation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provide basic analysis without AI.

        Args:
            investigation_data: Investigation data

        Returns:
            Basic diagnosis dictionary
        """
        logger.info("Performing basic analysis without AI")

        # Identify the most critical issue
        critical_issues = []

        # Check pods
        pods_data = investigation_data.get("pods", {})
        if not pods_data.get("healthy"):
            for pod in pods_data.get("problematic_pods", []):
                critical_issues.append(f"Pod {pod['name']} is {pod['status']}")

        # Check deployments
        deployments_data = investigation_data.get("deployments", {})
        if not deployments_data.get("healthy"):
            for deployment in deployments_data.get("problematic_deployments", []):
                critical_issues.append(f"Deployment {deployment['name']} has issues: {', '.join(deployment['issues'])}")

        # Check network
        network_data = investigation_data.get("network", {})
        if not network_data.get("healthy"):
            for service in network_data.get("problematic_services", []):
                critical_issues.append(f"Service {service['name']} has issues: {', '.join(service['issues'])}")

        # Build basic diagnosis
        if critical_issues:
            root_cause = f"Multiple issues detected: {'; '.join(critical_issues[:3])}"
            explanation = "Kubernetes cluster has unhealthy resources. Review individual component status for details."
            fix = "1. Check pod logs for error details\n2. Review deployment status\n3. Verify service connectivity\n4. Check recent events for cluster issues"
            confidence = 40  # Lower confidence for basic analysis
        else:
            root_cause = "No critical issues detected in the investigation"
            explanation = "All inspected components appear healthy. Further investigation may be needed for subtle issues."
            fix = "No immediate fixes required. Monitor cluster for any changes."
            confidence = 30

        return {
            "root_cause": root_cause,
            "explanation": explanation,
            "fix": fix,
            "kubectl_commands": [
                "kubectl get pods -A",
                "kubectl get events -A --sort-by=.metadata.creationTimestamp",
                "kubectl get deployments -A"
            ],
            "prevention": "Regular monitoring and alerting can help prevent issues. Set up proper resource limits and health checks.",
            "confidence": confidence,
            "confidence_reasoning": "Basic analysis without AI - confidence limited to pattern matching",
            "ai_generated": False,
            "investigation_summary": self._create_investigation_summary(investigation_data)
        }

    def _basic_targeted_analysis(
        self,
        resource_name: str,
        resource_type: str,
        investigation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Provide basic targeted analysis without AI.

        Args:
            resource_name: Name of the resource
            resource_type: Type of resource
            investigation_data: Investigation data

        Returns:
            Basic diagnosis dictionary
        """
        logger.info(f"Performing basic targeted analysis for {resource_type}/{resource_name}")

        return {
            "root_cause": f"Analysis for {resource_type}/{resource_name} requires AI for detailed diagnosis",
            "explanation": "Basic analysis available. Enable AI for detailed root cause analysis and fix recommendations.",
            "fix": f"Use kubectl describe {resource_type} {resource_name} for detailed information",
            "kubectl_commands": [
                f"kubectl describe {resource_type} {resource_name}",
                f"kubectl get {resource_type} {resource_name} -o yaml"
            ],
            "prevention": "Regular monitoring and health checks can prevent resource issues.",
            "confidence": 25,
            "confidence_reasoning": "Basic analysis without AI - limited diagnostic capability",
            "ai_generated": False,
            "resource_name": resource_name,
            "resource_type": resource_type,
            "investigation_summary": {}
        }

    def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the AI agent.

        Returns:
            Dictionary with health status
        """
        llm_health = self.llm_client.health_check()

        return {
            "ai_agent": "healthy",
            "llm_configured": llm_health.get("configured", False),
            "llm_model": llm_health.get("model", "unknown"),
            "prompt_builder": "healthy",
            "capabilities": [
                "root_cause_analysis",
                "fix_recommendation",
                "confidence_scoring",
                "kubectl_command_generation"
            ]
        }