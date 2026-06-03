import re
from typing import List, Dict, Any
from pathlib import Path
import json

MENU_PATH = Path.cwd() / "menu.json"
_MENU = None

def load_menu():
    global _MENU
    if _MENU is None:
        with open(MENU_PATH, "r", encoding="utf-8") as f:
            _MENU = json.load(f)
    return _MENU


def _all_item_names(menu: Dict[str, Any]) -> List[str]:
    """Flatten all item names from the nested menu categories structure."""
    names = []
    for cat in menu.get("menu", {}).get("categories", []):
        for item in cat.get("items", []):
            names.append(item.get("name", "").lower())
    return names


def sanitize_for_tts(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"[*_`~>#-]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


# Keywords that indicate off-topic responses
_OFF_TOPIC_KW = [
    "weather", "who is", "capital of", "president", "politics",
    "stock price", "news", "sports", "recipe for",
]


def guardrail_check(response_text: str, menu: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns {allowed: bool, reason: str | None}.
    Checks:
    - Off-topic keyword detection
    - Response length limit (60 words)
    """
    text_l = response_text.lower()

    for kw in _OFF_TOPIC_KW:
        if kw in text_l:
            return {"allowed": False, "reason": "off_topic"}

    if len(response_text.split()) > 60:
        return {"allowed": False, "reason": "too_long"}

    return {"allowed": True, "reason": None}


def compute_drift_score(response_text: str, menu: Dict[str, Any]) -> float:
    """
    Score 0.0-1.0 representing how on-menu the assistant reply is.
    Logic:
      - Start at base 0.5
      - +0.4 if any menu item name appears in the reply
      - -0.4 if off-topic keywords detected
      - +0.1 if ordering-related words present (order, price, total, etc.)
      - Clamp to [0.0, 1.0]
    """
    text_l = response_text.lower()
    score = 0.5

    # Reward menu item mentions
    item_names = _all_item_names(menu)
    if any(name in text_l for name in item_names if name):
        score += 0.4

    # Reward ordering-related language
    order_words = ["order", "price", "total", "bagel", "sandwich", "would you like",
                   "anything else", "can i get", "how many", "add"]
    if any(w in text_l for w in order_words):
        score += 0.1

    # Penalise off-topic keywords
    for kw in _OFF_TOPIC_KW:
        if kw in text_l:
            score -= 0.4
            break

    return round(max(0.0, min(1.0, score)), 2)
