import json
import re
import requests
from pathlib import Path
from .utils import RAW_DIR, info, ok, err

API_SHARE = "https://chat.deepseek.com/api/v0/share/content"
API_SESSION = "https://chat.deepseek.com/api/v0/chat/history_messages"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
    ),
    "Accept": "application/json, */*",
    "Accept-Language": "ar,en;q=0.9",
}


def parse_id(value: str) -> tuple[str, str]:
    m = re.search(r"/share/([a-z0-9]+)", value)
    if m:
        return m.group(1), "share"
    m = re.search(r"/s/([a-z0-9]+)", value)
    if m:
        return m.group(1), "session"
    return value.strip(), "share"


def fetch(value: str, token: str | None = None) -> Path:
    sid, kind = parse_id(value)
    info(f"ID: {sid}  |  النوع: {kind}")

    if kind == "share":
        headers = {**HEADERS, "Referer": f"https://chat.deepseek.com/share/{sid}"}
        r = requests.get(API_SHARE, params={"share_id": sid}, headers=headers, timeout=180)
    else:
        if not token:
            err("session يحتاج token (--token)")
            raise SystemExit(1)
        headers = {**HEADERS, "authorization": token, "Referer": f"https://chat.deepseek.com/a/chat/s/{sid}"}
        r = requests.get(API_SESSION, params={"chat_session_id": sid}, headers=headers, timeout=180)

    r.raise_for_status()
    data = r.json()

    if data.get("code") != 0:
        err(f"API error: {data.get('msg')}")
        raise SystemExit(1)

    out = RAW_DIR / f"{sid}.json"
    out.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    ok(f"تم الحفظ: {out}")
    return out
