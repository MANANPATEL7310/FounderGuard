"""Playbook Knowledge Base loader and matcher."""
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from backend.config import BASE_DIR

PLAYBOOK_JSON_PATH = BASE_DIR / "playbook" / "playbook_data.json"


class PlaybookKnowledgeBase:
    def __init__(self, json_path: Path = PLAYBOOK_JSON_PATH):
        self.json_path = Path(json_path)
        self.items: List[Dict[str, Any]] = []
        self._by_id: Dict[str, Dict[str, Any]] = {}
        self._by_theme: Dict[str, List[Dict[str, Any]]] = {}
        self.load()

    def load(self) -> None:
        if not self.json_path.exists():
            return
        with open(self.json_path, "r", encoding="utf-8") as f:
            self.items = json.load(f)

        self._by_id = {item["id"]: item for item in self.items}
        self._by_theme = {}
        for item in self.items:
            theme = item.get("theme", "general")
            self._by_theme.setdefault(theme, []).append(item)

    def get_by_id(self, item_id: str) -> Optional[Dict[str, Any]]:
        return self._by_id.get(item_id)

    def find_playbook_item(self, theme: str, stage: str = "idea") -> Optional[Dict[str, Any]]:
        """Finds the best matching playbook chunk for a given theme and operational stage."""
        candidates = self._by_theme.get(theme, [])
        if not candidates:
            # Fallback theme mappings
            fallback_themes = {
                "product_market_fit": ["validation_evidence", "market_demand"],
                "market_demand": ["validation_evidence", "idea_clarity"],
                "unit_economics_pricing": ["weak_business_model"],
                "weak_business_model": ["unit_economics_pricing"],
                "funding_cashflow": ["execution_hurdles"],
                "acquisition_retention": ["market_demand"],
            }
            for fb_theme in fallback_themes.get(theme, []):
                candidates = self._by_theme.get(fb_theme, [])
                if candidates:
                    break

        if not candidates:
            return self.items[0] if self.items else None

        # Filter by stage
        stage_matches = [c for c in candidates if stage in c.get("stages", [])]
        if stage_matches:
            return stage_matches[0]
        return candidates[0]


# Singleton instance
playbook_kb = PlaybookKnowledgeBase()
