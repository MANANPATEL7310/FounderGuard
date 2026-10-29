"""Thread-safe evaluation storage with versioning, lineage tracking, and deletion."""
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class EvaluationStorage:
    def __init__(self):
        self._lock = threading.Lock()
        self._evaluations: Dict[str, Dict[str, Any]] = {}
        # Map root_id -> list of evaluation_ids in chronological version order
        self._lineages: Dict[str, List[str]] = {}

    def create(
        self,
        eval_id: str,
        normalized: Dict[str, Any],
        raw_submission: Optional[Dict[str, Any]] = None,
        consent: bool = True,
    ) -> Dict[str, Any]:
        with self._lock:
            record = {
                "id": eval_id,
                "parent_id": None,
                "version": 1,
                "root_id": eval_id,
                "consent": consent,
                "status": "queued",
                "stage": "queued",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": None,
                "raw_submission": raw_submission or {},
                "normalized": normalized,
                "envelopes": {},
                "report": None,
                "recommendations": None,
                "clarifications": [],
                "error": None,
            }
            self._evaluations[eval_id] = record
            self._lineages[eval_id] = [eval_id]
            return dict(record)

    def create_version(
        self,
        parent_id: str,
        new_eval_id: str,
        normalized: Dict[str, Any],
        raw_submission: Optional[Dict[str, Any]] = None,
        clarifications: Optional[List[Dict[str, str]]] = None,
    ) -> Optional[Dict[str, Any]]:
        with self._lock:
            parent = self._evaluations.get(parent_id)
            if not parent:
                return None

            root_id = parent.get("root_id") or parent_id
            current_versions = self._lineages.get(root_id, [parent_id])
            version_number = len(current_versions) + 1

            record = {
                "id": new_eval_id,
                "parent_id": parent_id,
                "version": version_number,
                "root_id": root_id,
                "consent": parent.get("consent", True),
                "status": "queued",
                "stage": "queued",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "completed_at": None,
                "raw_submission": raw_submission or parent.get("raw_submission", {}),
                "normalized": normalized,
                "envelopes": {},
                "report": None,
                "recommendations": None,
                "clarifications": clarifications or [],
                "error": None,
            }
            self._evaluations[new_eval_id] = record
            current_versions.append(new_eval_id)
            self._lineages[root_id] = current_versions
            return dict(record)

    def get(self, eval_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            rec = self._evaluations.get(eval_id)
            if rec:
                return dict(rec)
            return None

    def get_lineage(self, eval_id: str) -> List[Dict[str, Any]]:
        """Returns all versions belonging to the same evaluation lineage."""
        with self._lock:
            rec = self._evaluations.get(eval_id)
            if not rec:
                return []
            root_id = rec.get("root_id") or eval_id
            version_ids = self._lineages.get(root_id, [eval_id])
            results = []
            for vid in version_ids:
                v_rec = self._evaluations.get(vid)
                if v_rec:
                    results.append({
                        "evaluation_id": vid,
                        "version": v_rec.get("version", 1),
                        "parent_id": v_rec.get("parent_id"),
                        "status": v_rec.get("status"),
                        "created_at": v_rec.get("created_at"),
                    })
            return results

    def set_stage(self, eval_id: str, stage: str, status: Optional[str] = None) -> None:
        with self._lock:
            if eval_id in self._evaluations:
                self._evaluations[eval_id]["stage"] = stage
                if status:
                    self._evaluations[eval_id]["status"] = status

    def update_envelopes_and_report(
        self,
        eval_id: str,
        envelopes: Dict[str, Any],
        report: Any,
        status: str = "report_ready",
        stage: str = "generating_recommendations",
    ) -> None:
        with self._lock:
            if eval_id in self._evaluations:
                self._evaluations[eval_id]["envelopes"] = envelopes
                self._evaluations[eval_id]["report"] = report
                self._evaluations[eval_id]["status"] = status
                self._evaluations[eval_id]["stage"] = stage

    def update_recommendations(
        self,
        eval_id: str,
        recommendations: Any,
        status: str = "complete",
        stage: str = "complete",
    ) -> None:
        with self._lock:
            if eval_id in self._evaluations:
                self._evaluations[eval_id]["recommendations"] = recommendations
                self._evaluations[eval_id]["status"] = status
                self._evaluations[eval_id]["stage"] = stage
                self._evaluations[eval_id]["completed_at"] = datetime.now(timezone.utc).isoformat()

    def set_failed(self, eval_id: str, error_msg: str) -> None:
        with self._lock:
            if eval_id in self._evaluations:
                self._evaluations[eval_id]["status"] = "failed"
                self._evaluations[eval_id]["stage"] = "failed"
                self._evaluations[eval_id]["error"] = error_msg
                self._evaluations[eval_id]["completed_at"] = datetime.now(timezone.utc).isoformat()

    def delete(self, eval_id: str, delete_lineage: bool = True) -> bool:
        """
        Deletes evaluation data from storage completely.
        If delete_lineage is True, deletes all versions associated with the root lineage.
        """
        with self._lock:
            if eval_id not in self._evaluations:
                return False

            rec = self._evaluations[eval_id]
            root_id = rec.get("root_id") or eval_id

            if delete_lineage and root_id in self._lineages:
                for vid in list(self._lineages[root_id]):
                    self._evaluations.pop(vid, None)
                self._lineages.pop(root_id, None)
            else:
                self._evaluations.pop(eval_id, None)
                if root_id in self._lineages and eval_id in self._lineages[root_id]:
                    self._lineages[root_id].remove(eval_id)

            return True


# Global store singleton
storage = EvaluationStorage()
