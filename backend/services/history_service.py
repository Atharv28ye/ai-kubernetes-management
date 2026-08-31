from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime, timezone
from threading import Lock
import json
from loguru import logger


class HistoryService:
    """
    Simple persistent investigation history service.

    Investigation results are stored locally in JSON so the frontend
    does not depend on InsForge database APIs.
    """

    def __init__(self, storage_file: Optional[str] = None):
        backend_dir = Path(__file__).resolve().parent.parent

        self.storage_file = Path(
            storage_file
            or backend_dir / "data" / "investigation_history.json"
        )

        self.storage_file.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self._lock = Lock()

        if not self.storage_file.exists():
            self._write_history([])

        logger.info(
            f"History service initialized: {self.storage_file}"
        )

    def _read_history(self) -> List[Dict[str, Any]]:
        """Read investigation history from disk."""

        try:
            if not self.storage_file.exists():
                return []

            with open(
                self.storage_file,
                "r",
                encoding="utf-8"
            ) as file:
                data = json.load(file)

            if not isinstance(data, list):
                return []

            return data

        except (json.JSONDecodeError, OSError) as e:
            logger.error(
                f"Failed to read investigation history: {e}"
            )
            return []

    def _write_history(
        self,
        history: List[Dict[str, Any]]
    ) -> None:
        """Write investigation history to disk."""

        try:
            with open(
                self.storage_file,
                "w",
                encoding="utf-8"
            ) as file:
                json.dump(
                    history,
                    file,
                    indent=2,
                    ensure_ascii=False
                )

        except OSError as e:
            logger.error(
                f"Failed to write investigation history: {e}"
            )
            raise

    def save_investigation(
        self,
        investigation_id: str,
        cluster: str,
        namespace: str,
        diagnosis: Optional[Dict[str, Any]],
        status: str = "completed"
    ) -> Dict[str, Any]:
        """
        Save a completed investigation.
        """

        diagnosis = diagnosis or {}

        record = {
            "id": investigation_id,
            "cluster": cluster,
            "root_cause": diagnosis.get(
                "root_cause",
                "No issues detected"
            ),
            "explanation": diagnosis.get(
                "explanation",
                ""
            ),
            "fix": diagnosis.get(
                "fix",
                ""
            ),
            "kubectl_commands": diagnosis.get(
                "kubectl_commands",
                []
            ),
            "confidence": diagnosis.get(
                "confidence",
                0
            ),
            "confidence_reasoning": diagnosis.get(
                "confidence_reasoning",
                ""
            ),
            "prevention": diagnosis.get(
                "prevention",
                ""
            ),
            "namespace": namespace,
            "status": status,
            "created_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "ai_generated": diagnosis.get(
                "ai_generated",
                False
            )
        }

        with self._lock:
            history = self._read_history()

            # Avoid duplicate records for the same investigation.
            history = [
                item
                for item in history
                if item.get("id") != investigation_id
            ]

            history.insert(0, record)

            # Keep the most recent 100 investigations.
            history = history[:100]

            self._write_history(history)

        logger.info(
            f"Investigation saved to history: {investigation_id}"
        )

        return record

    def get_history(
        self,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Return the most recent investigations."""

        limit = max(1, min(limit, 100))

        with self._lock:
            history = self._read_history()

        return history[:limit]

    def get_investigation(
        self,
        investigation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Return one investigation by ID."""

        with self._lock:
            history = self._read_history()

        for item in history:
            if item.get("id") == investigation_id:
                return item

        return None

    def clear_history(self) -> None:
        """Clear all stored investigation history."""

        with self._lock:
            self._write_history([])

        logger.info("Investigation history cleared")