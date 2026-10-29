"""Operational metrics and request tracking implementing Section 4.10."""
import threading
import time
from typing import Any, Dict, List


class OperationalMetrics:
    def __init__(self):
        self._lock = threading.Lock()
        self.request_counts: Dict[str, int] = {}
        self.error_counts: Dict[str, int] = {}
        self.model_latencies: Dict[str, List[float]] = {
            "model_a": [],
            "model_b": [],
            "model_c": [],
            "model_d": [],
            "llm": [],
        }
        self.warning_counts: Dict[str, int] = {}
        self.ood_flags_count: int = 0
        self.not_applicable_counts: Dict[str, int] = {
            "model_a": 0,
            "model_b": 0,
            "model_c": 0,
            "model_d": 0,
        }
        self.recommendation_methods: Dict[str, int] = {
            "llm_direct": 0,
            "llm_repaired": 0,
            "template_playbook": 0,
        }

    def record_request(self, endpoint: str, status_code: int) -> None:
        with self._lock:
            key = f"{endpoint} [{status_code}]"
            self.request_counts[key] = self.request_counts.get(key, 0) + 1
            if status_code >= 400:
                self.error_counts[key] = self.error_counts.get(key, 0) + 1

    def record_model_latency(self, model_id: str, runtime_ms: float) -> None:
        with self._lock:
            if model_id in self.model_latencies:
                # Keep rolling window of last 100 observations
                self.model_latencies[model_id].append(round(runtime_ms, 2))
                if len(self.model_latencies[model_id]) > 100:
                    self.model_latencies[model_id].pop(0)

    def record_model_status(self, model_id: str, status: str, warnings: List[str] = None) -> None:
        with self._lock:
            if status == "not_applicable":
                self.not_applicable_counts[model_id] = self.not_applicable_counts.get(model_id, 0) + 1
            if warnings:
                for w in warnings:
                    w_tag = w.split(":")[0][:50]
                    self.warning_counts[w_tag] = self.warning_counts.get(w_tag, 0) + 1

    def record_ood_flag(self) -> None:
        with self._lock:
            self.ood_flags_count += 1

    def record_recommendation_method(self, method: str) -> None:
        with self._lock:
            self.recommendation_methods[method] = self.recommendation_methods.get(method, 0) + 1

    def get_summary(self) -> Dict[str, Any]:
        with self._lock:
            avg_latencies = {}
            for m, lats in self.model_latencies.items():
                avg_latencies[m] = round(sum(lats) / len(lats), 2) if lats else 0.0

            return {
                "total_requests_tracked": sum(self.request_counts.values()),
                "requests_by_endpoint": dict(self.request_counts),
                "errors_by_endpoint": dict(self.error_counts),
                "average_model_latencies_ms": avg_latencies,
                "not_applicable_counts": dict(self.not_applicable_counts),
                "warning_occurrences": dict(self.warning_counts),
                "out_of_distribution_triggers": self.ood_flags_count,
                "recommendation_methods_breakdown": dict(self.recommendation_methods),
            }


# Global metrics tracker singleton
metrics = OperationalMetrics()
