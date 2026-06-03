import re
from typing import List, Dict, Any
from pathlib import Path
import json
import re

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


def extract_order_from_text(resp_text: str, menu: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attempt to extract a structured order from `resp_text`.
    Strategy:
      1. Try to find a JSON blob in the text and parse it. Validate items against the menu.
      2. If no valid JSON, use a regex fallback to find patterns like "2 plain bagels".

    Returns a dict: {"items": [{"name", "quantity", "price"}], "total": number}
    Unknown items are ignored.
    """
    order = {"items": [], "total": 0.0}
    if not resp_text:
        return order

    # normalize menu map: name(lower) -> item dict
    menu_map = {}
    for cat in menu.get("menu", {}).get("categories", []):
        for item in cat.get("items", []):
            name = item.get("name", "").strip().lower()
            if name:
                menu_map[name] = item

    # 1) try JSON blob
    m = re.search(r"\{.*\}", resp_text, flags=re.S)
    if m:
        try:
            j = json.loads(m.group(0))
            items = []
            for it in j.get("items", []) if isinstance(j, dict) else []:
                name = (it.get("name") or "").strip().lower()
                if name in menu_map:
                    qty = int(it.get("quantity", 1))
                    # menu uses base_price
                    price = float(menu_map[name].get("base_price", it.get("price", 0.0) or 0.0))
                    items.append({"name": menu_map[name]["name"], "quantity": qty, "price": price})
            if items:
                total = sum(i["quantity"] * i["price"] for i in items)
                return {"items": items, "total": round(total, 2)}
        except Exception:
            pass

    # 2) regex fallback: look for patterns like '2 plain bagels'
    found = []
    text_l = resp_text.lower()
    # sort menu names by length so longer names match first
    names_sorted = sorted(menu_map.keys(), key=lambda x: -len(x))
    for name in names_sorted:
        pattern = r"(\d+)\s+" + re.escape(name)
        for qty in re.findall(pattern, text_l):
            q = int(qty)
            price = float(menu_map[name].get("base_price", 0.0) or 0.0)
            found.append({"name": menu_map[name]["name"], "quantity": q, "price": price})

    if found:
        total = sum(i["quantity"] * i["price"] for i in found)
        return {"items": found, "total": round(total, 2)}

    return order
