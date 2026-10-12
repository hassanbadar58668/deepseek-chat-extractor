import json
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def get_messages(data: dict) -> list:
    d = data.get("data", {})
    if "biz_data" in d:
        return d["biz_data"].get("messages", [])
    if "chat_messages" in d:
        return d["chat_messages"]
    if "messages" in d:
        return d["messages"]
    return []


def get_title(data: dict) -> str:
    try:
        return data["data"]["biz_data"].get("title", "chat")
    except Exception:
        return data.get("data", {}).get("title", "chat")
