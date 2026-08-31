
from typing import Dict, Any, List
from loguru import logger
from datetime import datetime, timedelta, timezone
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


class EventsAnalyzer:
    """Analyzes Kubernetes events for issues."""

    # Event types/reasons to detect
    PROBLEMATIC_EVENT_TYPES = [
        "FailedScheduling",
        "BackOff",
        "FailedMount",
        "FailedPull",
        "ErrImagePull",
        "Unhealthy",
        "Failed",
        "Warning",
        "Error"
    ]

    def __init__(
        self,
        kubectl_executor: KubectlExecutor,
        lookback_hours: int = 24
    ):
        """
        Initialize events analyzer.

        Args:
            kubectl_executor: KubectlExecutor instance
            lookback_hours: How many hours back to look for events
        """
        self.kubectl = kubectl_executor
        self.lookback_hours = lookback_hours

    def analyze_events(self, namespace: str = "all") -> Dict[str, Any]:
        """
        Analyze Kubernetes events across all or specific namespace.

        Args:
            namespace: Namespace to analyze ("all" for all namespaces)

        Returns:
            Dictionary with event analysis results
        """

        logger.info(
            f"Analyzing events in namespace: {namespace}"
        )

        # Build kubectl command
        ns_flag = "-A" if namespace == "all" else f"-n {namespace}"
        command = f"get events {ns_flag} -o json"

        result = self.kubectl.execute_json(command)

        if not result["success"]:
            logger.error(
                f"Failed to get events: {result['error']}"
            )

            return {
                "success": False,
                "error": result["error"],
                "problematic_events": []
            }

        events_data = result["data"]
        problematic_events = []

        # ---------------------------------------------------------
        # IMPORTANT:
        # Kubernetes timestamps are timezone-aware (usually UTC).
        # Therefore the cutoff time must also be timezone-aware.
        # ---------------------------------------------------------
        cutoff_time = (
            datetime.now(timezone.utc)
            - timedelta(hours=self.lookback_hours)
        )

        # Process each event
        for item in events_data.get("items", []):

            event_type = item.get("type", "Normal")
            event_reason = item.get("reason", "")
            event_message = item.get("message", "")

            # Check if event is problematic
            is_problematic = (
                event_type in ["Warning", "Error"]
                or event_reason in self.PROBLEMATIC_EVENT_TYPES
            )

            if not is_problematic:
                continue

            # Kubernetes normally provides lastTimestamp.
            # Some newer Kubernetes event formats may use
            # eventTime instead, so try both.
            event_time_str = (
                item.get("lastTimestamp")
                or item.get("eventTime")
                or item.get("firstTimestamp")
                or ""
            )

            try:
                if not event_time_str:
                    raise ValueError(
                        "Event does not contain a timestamp"
                    )

                # Convert Kubernetes ISO-8601 timestamp to
                # a timezone-aware datetime.
                event_time = self._parse_timestamp(
                    event_time_str
                )

                # Both event_time and cutoff_time are now
                # timezone-aware UTC datetimes.
                if event_time >= cutoff_time:

                    problematic_events.append(
                        self._build_event_record(
                            item,
                            event_type,
                            event_reason,
                            event_message,
                            event_time_str
                        )
                    )

                    logger.warning(
                        f"Found problematic event: "
                        f"{event_reason} - "
                        f"{event_message[:100]}"
                    )

            except (ValueError, TypeError, AttributeError) as e:

                logger.warning(
                    f"Failed to parse event timestamp "
                    f"'{event_time_str}': {e}"
                )

                # Include problematic events even if timestamp
                # parsing fails, so we don't silently lose useful
                # Kubernetes diagnostic information.
                problematic_events.append(
                    self._build_event_record(
                        item,
                        event_type,
                        event_reason,
                        event_message,
                        event_time_str
                    )
                )

        # Group events by reason for summary
        event_summary = self._summarize_events(
            problematic_events
        )

        logger.info(
            f"Event analysis complete. "
            f"Found {len(problematic_events)} "
            f"problematic events"
        )

        return {
            "success": True,
            "problematic_events": problematic_events,
            "event_summary": event_summary,
            "total_events_analyzed": len(
                events_data.get("items", [])
            ),
            "lookback_hours": self.lookback_hours
        }

    @staticmethod
    def _parse_timestamp(timestamp: str) -> datetime:
        """
        Parse a Kubernetes ISO-8601 timestamp.

        Returns:
            Timezone-aware datetime in UTC.

        Examples:
            2026-08-29T10:20:30Z
            2026-08-29T10:20:30+00:00
        """

        timestamp = timestamp.strip()

        # Kubernetes commonly uses "Z" to indicate UTC.
        if timestamp.endswith("Z"):
            timestamp = timestamp[:-1] + "+00:00"

        parsed = datetime.fromisoformat(timestamp)

        # If the timestamp somehow has no timezone,
        # explicitly treat it as UTC.
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        # Convert everything to UTC for consistent comparison.
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _build_event_record(
        item: Dict[str, Any],
        event_type: str,
        event_reason: str,
        event_message: str,
        event_time_str: str
    ) -> Dict[str, Any]:
        """
        Build a standardized problematic-event record.
        """

        metadata = item.get("metadata", {})
        involved_object = item.get(
            "involvedObject",
            {}
        )

        return {
            "type": event_type,
            "reason": event_reason,
            "message": event_message,
            "namespace": metadata.get(
                "namespace",
                "unknown"
            ),
            "involved_object": {
                "kind": involved_object.get(
                    "kind",
                    ""
                ),
                "name": involved_object.get(
                    "name",
                    ""
                ),
                "namespace": involved_object.get(
                    "namespace",
                    ""
                )
            },
            "timestamp": event_time_str,
            "count": item.get("count", 1)
        }

    def _summarize_events(
        self,
        events: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        Summarize events by reason.

        Args:
            events: List of event dictionaries

        Returns:
            Dictionary with event counts by reason
        """

        summary = {}

        for event in events:

            reason = event.get(
                "reason",
                "Unknown"
            )

            count = event.get(
                "count",
                1
            )

            if reason in summary:
                summary[reason] += count
            else:
                summary[reason] = count

        return summary

    def get_events_for_resource(
        self,
        resource_name: str,
        resource_type: str = "Pod",
        namespace: str = "default"
    ) -> Dict[str, Any]:
        """
        Get events for a specific resource.

        Args:
            resource_name: Name of the resource
            resource_type: Type of resource
            namespace: Namespace of the resource

        Returns:
            Dictionary with events for the resource
        """

        logger.info(
            f"Getting events for "
            f"{resource_type}/{resource_name} "
            f"in {namespace}"
        )

        command = (
            f"get events "
            f"-n {namespace} "
            f"--field-selector "
            f"involvedObject.name={resource_name},"
            f"involvedObject.kind={resource_type} "
            f"-o json"
        )

        result = self.kubectl.execute_json(command)

        if not result["success"]:
            return {
                "success": False,
                "error": result["error"],
                "events": []
            }

        events_data = result["data"]
        events = []

        for item in events_data.get("items", []):

            events.append({
                "type": item.get(
                    "type",
                    "Normal"
                ),
                "reason": item.get(
                    "reason",
                    ""
                ),
                "message": item.get(
                    "message",
                    ""
                ),
                "timestamp": (
                    item.get("lastTimestamp")
                    or item.get("eventTime")
                    or item.get("firstTimestamp")
                    or ""
                ),
                "count": item.get(
                    "count",
                    1
                )
            })

        return {
            "success": True,
            "resource_name": resource_name,
            "resource_type": resource_type,
            "namespace": namespace,
            "events": events
        }

