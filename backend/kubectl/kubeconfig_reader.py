import os
import yaml
from typing import Dict, Any, List, Optional
from loguru import logger


class KubeconfigReader:
    """Reads and manages Kubernetes kubeconfig files."""

    def __init__(self, kubeconfig_path: Optional[str] = None):
        """
        Initialize kubeconfig reader.

        Args:
            kubeconfig_path: Path to kubeconfig file.
        """
        self.kubeconfig_path = (
            kubeconfig_path
            or os.getenv("KUBECONFIG_PATH")
            or os.path.expanduser("~/.kube/config")
        )

    def _load_config(self) -> Optional[Dict[str, Any]]:
        """Load kubeconfig YAML file."""

        if not os.path.exists(self.kubeconfig_path):
            logger.error(
                f"Kubeconfig file not found: {self.kubeconfig_path}"
            )
            return None

        try:
            with open(self.kubeconfig_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

            if not config:
                logger.error("Kubeconfig is empty")
                return None

            return config

        except Exception as e:
            logger.error(
                f"Failed to read kubeconfig: {str(e)}"
            )
            return None

    def _contexts_to_dict(
        self,
        contexts_data: Any
    ) -> Dict[str, Dict[str, Any]]:
        """Convert kubeconfig contexts into a dictionary."""

        if isinstance(contexts_data, list):
            return {
                item.get("name"): item
                for item in contexts_data
                if isinstance(item, dict) and item.get("name")
            }

        if isinstance(contexts_data, dict):
            return contexts_data

        return {}

    def _clusters_to_dict(
        self,
        clusters_data: Any
    ) -> Dict[str, Dict[str, Any]]:
        """Convert kubeconfig clusters into a dictionary."""

        if isinstance(clusters_data, list):
            return {
                item.get("name"): item
                for item in clusters_data
                if isinstance(item, dict) and item.get("name")
            }

        if isinstance(clusters_data, dict):
            return clusters_data

        return {}

    def get_clusters(self) -> List[Dict[str, Any]]:
        """
        Get available Kubernetes contexts/clusters.

        Returns:
            List of cluster information dictionaries.
        """

        config = self._load_config()

        if not config:
            return []

        try:
            clusters_dict = self._clusters_to_dict(
                config.get("clusters", [])
            )

            contexts_dict = self._contexts_to_dict(
                config.get("contexts", [])
            )

            current_context = config.get("current-context")

            clusters = []

            for context_name, context_info in contexts_dict.items():

                if not isinstance(context_info, dict):
                    continue

                context_config = context_info.get(
                    "context",
                    {}
                )

                cluster_name = context_config.get(
                    "cluster"
                )

                cluster_info = clusters_dict.get(
                    cluster_name,
                    {}
                )

                cluster_config = cluster_info.get(
                    "cluster",
                    {}
                )

                server = cluster_config.get(
                    "server",
                    "Unknown"
                )

                clusters.append({
                    "name": context_name,
                    "cluster": cluster_name,
                    "is_current": (
                        context_name == current_context
                    ),
                    "server": server,
                })

            logger.info(
                f"Found {len(clusters)} clusters in kubeconfig"
            )

            return clusters

        except Exception as e:
            logger.error(
                f"Failed to parse clusters: {str(e)}"
            )
            return []

    def get_current_context(self) -> Optional[str]:
        """
        Get the current Kubernetes context.

        Returns:
            Current context name or None.
        """

        config = self._load_config()

        if not config:
            return None

        return config.get("current-context")

    def set_context(self, context_name: str) -> bool:
        """
        Set the current Kubernetes context.

        Args:
            context_name:
                Name of the context to switch to.

        Returns:
            True if successful, False otherwise.
        """

        config = self._load_config()

        if not config:
            return False

        try:
            contexts = self._contexts_to_dict(
                config.get("contexts", [])
            )

            # Validate that the requested context exists.
            if context_name not in contexts:
                logger.error(
                    f"Context '{context_name}' not found in kubeconfig"
                )

                logger.info(
                    f"Available contexts: "
                    f"{list(contexts.keys())}"
                )

                return False

            # Update current context.
            config["current-context"] = context_name

            # Write the modified kubeconfig back.
            with open(
                self.kubeconfig_path,
                "w",
                encoding="utf-8"
            ) as f:
                yaml.safe_dump(
                    config,
                    f,
                    default_flow_style=False,
                    sort_keys=False
                )

            logger.info(
                f"Successfully switched context to: "
                f"{context_name}"
            )

            return True

        except Exception as e:
            logger.error(
                f"Failed to set context '{context_name}': "
                f"{str(e)}"
            )

            return False