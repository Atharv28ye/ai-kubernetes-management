import subprocess
import json
from typing import Optional, Dict, Any
from loguru import logger
import os


class KubectlExecutor:
    """Reusable utility to safely execute kubectl commands."""
    
    def __init__(self, kubeconfig_path: Optional[str] = None, timeout: Optional[int] = None):
        """
        Initialize kubectl executor.
        
        Args:
            kubeconfig_path: Optional path to kubeconfig file
            timeout: Default timeout for kubectl commands in seconds (reads from env var if not provided)
        """
        self.kubeconfig_path = kubeconfig_path
        self.default_timeout = timeout or int(os.getenv("KUBECTL_TIMEOUT", "60"))
        
    def _build_command(self, command: str) -> list[str]:
        """Build the full kubectl command with optional kubeconfig."""
        cmd = ["kubectl"]
        
        if self.kubeconfig_path:
            cmd.extend(["--kubeconfig", self.kubeconfig_path])
        
        # Split the command into parts
        cmd.extend(command.split())
        return cmd
    
    def execute(
        self,
        command: str,
        capture_output: bool = True,
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Execute a kubectl command.
        
        Args:
            command: The kubectl command to execute (e.g., "get pods -A")
            capture_output: Whether to capture stdout/stderr
            timeout: Command timeout in seconds (defaults to instance timeout)
            
        Returns:
            Dictionary with success, stdout, stderr, and return_code
        """
        if timeout is None:
            timeout = self.default_timeout
        try:
            cmd = self._build_command(command)
            logger.info(f"Executing kubectl command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
            
            response = {
                "success": result.returncode == 0,
                "stdout": result.stdout if capture_output else "",
                "stderr": result.stderr if capture_output else "",
                "return_code": result.returncode,
                "command": command
            }
            
            if result.returncode != 0:
                logger.warning(f"Kubectl command failed: {result.stderr}")
                # Add friendly error messages for common kubectl errors
                friendly_error = self._get_friendly_error(result.stderr)
                if friendly_error:
                    response["friendly_error"] = friendly_error
            else:
                logger.info(f"Kubectl command succeeded")
                
            return response
            
        except subprocess.TimeoutExpired:
            logger.error(f"Kubectl command timed out after {timeout} seconds")
            return {
                "success": False,
                "stdout": "",
                "stderr": f"Command timed out after {timeout} seconds",
                "friendly_error": "Kubernetes command timed out. The cluster might be unresponsive.",
                "return_code": -1,
                "command": command
            }
        except FileNotFoundError:
            logger.error("kubectl command not found")
            return {
                "success": False,
                "stdout": "",
                "stderr": "kubectl command not found. Please ensure kubectl is installed and in your PATH.",
                "friendly_error": "kubectl is not installed or not accessible. Please install kubectl to continue.",
                "return_code": -1,
                "command": command
            }
        except Exception as e:
            logger.error(f"Error executing kubectl command: {str(e)}")
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "friendly_error": f"Failed to execute kubectl command: {str(e)}",
                "return_code": -1,
                "command": command
            }
    
    def _get_friendly_error(self, stderr: str) -> Optional[str]:
        """
        Get a friendly error message for common kubectl errors.
        
        Args:
            stderr: The stderr output from kubectl
            
        Returns:
            Friendly error message or None
        """
        stderr_lower = stderr.lower()
        
        if "unable to connect to the server" in stderr_lower or "dial tcp" in stderr_lower:
            return "Unable to connect to Kubernetes cluster. Please verify your kubeconfig and cluster access."
        elif "no such host" in stderr_lower:
            return "Kubernetes cluster endpoint not found. Please check your kubeconfig configuration."
        elif "certificate signed by unknown authority" in stderr_lower:
            return "Kubernetes certificate verification failed. Please check your cluster certificates."
        elif "access denied" in stderr_lower or "forbidden" in stderr_lower:
            return "Access denied. Please check your kubectl permissions and RBAC configuration."
        elif "context" in stderr_lower and "does not exist" in stderr_lower:
            return "Kubernetes context not found. Please check your kubeconfig contexts."
        elif "namespace" in stderr_lower and "not found" in stderr_lower:
            return "Kubernetes namespace not found. Please verify the namespace exists."
        elif "connection refused" in stderr_lower:
            return "Connection refused by Kubernetes cluster. The cluster might be down or inaccessible."
        
        return None
    
    def execute_json(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute a kubectl command and parse JSON output.
        
        Args:
            command: The kubectl command to execute (should include -o json)
            timeout: Command timeout in seconds
            
        Returns:
            Dictionary with success and parsed JSON data
        """
        result = self.execute(command, timeout=timeout)
        
        if not result["success"]:
            return {
                "success": False,
                "data": None,
                "error": result["stderr"]
            }
        
        try:
            data = json.loads(result["stdout"])
            return {
                "success": True,
                "data": data,
                "error": None
            }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON output: {str(e)}")
            return {
                "success": False,
                "data": None,
                "error": f"Failed to parse JSON: {str(e)}"
            }
