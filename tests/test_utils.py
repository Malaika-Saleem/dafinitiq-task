import pytest
from app.utils import guardrail_check, compute_drift_score, extract_order_from_text

from pathlib import Path
import json

MENU_PATH = Path.cwd() / "menu.json"
MENU = json.loads(MENU_PATH.read_text(encoding="utf-8"))


def test_guardrail_off_topic_and_length():
    # off-topic
    res = guardrail_check("What's the weather today?", MENU)
    assert not res["allowed"] and res["reason"] == "off_topic"

    # too long (>60 words)
    long_text = "word " * 61
    res2 = guardrail_check(long_text, MENU)
    assert not res2["allowed"] and res2["reason"] == "too_long"

    # acceptable short reply
    ok = guardrail_check("We have plain bagels and garlic knots.", MENU)
    assert ok["allowed"]


def test_compute_drift_score_item_and_order_words():
    # reply mentions a menu item
    s1 = compute_drift_score("I recommend Garlic Knots", MENU)
    assert s1 >= 0.9

    # off-topic reduces score
    s2 = compute_drift_score("The president is coming", MENU)
    assert s2 <= 0.2

    # ordering words add slight bonus
    s3 = compute_drift_score("Would you like to add a bagel to your order?", MENU)
    assert s3 >= 0.6


def test_extract_order_from_text_json_valid():
    # Build a JSON text using an item from menu.json
    text = '{"items": [{"name": "Plain Bagel", "quantity": 2}], "total": 0.0}'
    order = extract_order_from_text(text, MENU)
    assert order["items"] and order["items"][0]["name"] == "Plain Bagel"
    assert order["items"][0]["quantity"] == 2
    assert order["total"] > 0.0


def test_extract_order_from_text_json_unknown_item():
    text = '{"items": [{"name": "Nonexistent Item", "quantity": 2}], "total": 0.0}'
    order = extract_order_from_text(text, MENU)
    assert order["items"] == [] and order["total"] == 0.0


def test_extract_order_from_text_regex_fallback():
    text = "I'd like 2 plain bagels and 1 garlic knots please"
    order = extract_order_from_text(text, MENU)
    # should find at least plain bagels
    names = [i["name"].lower() for i in order["items"]]
    assert any("plain bagel" in n for n in names)
    assert order["total"] > 0
