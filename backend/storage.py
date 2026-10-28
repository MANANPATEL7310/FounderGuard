"""Thread-safe evaluation storage."""
import threading
from datetime import datetime, timezone
from typing import Any, Dict, Optional

class EvaluationStorage:
    def __init__(self):
        self._lock = threading.Lock()
        self._evaluations: Dict[str, Dict[str, Any]] = {}

    def create(self, eval_id: str, normalized: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            record = {
                "id": eval_id,
                "status": "queued",
                "stage": "queued",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": None,
                "normalized": normalized,
                "envelopes": {},
                "report": None,
                "recommendations": None,
                "error": None,
            }
            self._evaluations[eval_id] = record
            return record

    def get(self, eval_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            rec = self._evaluations.get(eval_id)
            if rec:
                return dict(rec)
            return None

    def update_envelopes_and_report(
        self,
        eval_id: str,
        envelopes: Dict[str, Any],
        report: Any,
        status: str = "report_ready"
    ) -> None:
        with self._lock:
            if eval_id in self._evaluations:
                self._evaluations[eval_id]["envelopes"] = envelopes
                self._evaluations[eval_id]["report"] = report
                self._evaluations[eval_id]["status"] = status
                self._evaluations[eval_id]["stage"] = "complete"
                self._evaluations[eval_id]["completed_at"] = datetime.now(timezone.utc).isoformat()

    def update_recommendations(self, eval_id: str, recommendations: Any) -> None:
        with self._lock:
            if eval_id in self._evaluations:
                self._evaluations[eval_id]["recommendations"] = recommendations

    def set_failed(self, eval_id: str, error_msg: str) -> None:
        with self._lock:
            if eval_id in self._evaluations:
                self._evaluations[eval_id]["status"] = "failed"
                self._evaluations[eval_id]["stage"] = "failed"
                self._evaluations[eval_id]["error"] = error_msg
                self._evaluations[eval_id]["completed_at"] = datetime.now(timezone.utc).isoformat()

    def delete(self, eval_id: str) -> bool:
        with self._lock:
            if eval_id in self._evaluations:
                del self._evaluations[eval_id]
                return True
            return False

# Global store singleton
storage = EvaluationStorage()

