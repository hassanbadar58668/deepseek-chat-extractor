from .parser import get_messages


def filter_messages(
    data: dict,
    only: str = "clean",
    last: int | None = None,
    range_spec: str | None = None,
    keyword: str | None = None,
) -> list[dict]:
    msgs = get_messages(data)

    if only == "code":
        msgs = [
            m for m in msgs
            if any("```" in (f.get("content") or "") for f in m.get("fragments", []))
        ]
    elif only == "thinking":
        msgs = [
            m for m in msgs
            if any(f.get("type") == "THINK" for f in m.get("fragments", []))
        ]
    elif only == "search":
        msgs = [
            m for m in msgs
            if any(f.get("type") in ("TOOL_SEARCH", "TOOL_OPEN") for f in m.get("fragments", []))
        ]
    elif only == "tools":
        msgs = [
            m for m in msgs
            if any((f.get("type") or "").startswith("TOOL_") for f in m.get("fragments", []))
        ]
    elif only == "user":
        msgs = [m for m in msgs if m.get("role") == "USER"]
    elif only == "assistant":
        msgs = [m for m in msgs if m.get("role") == "ASSISTANT"]

    if keyword:
        kw = keyword.lower()
        msgs = [
            m for m in msgs
            if any(kw in (f.get("content") or "").lower() for f in m.get("fragments", []))
        ]

    if last:
        msgs = msgs[-last:]
    elif range_spec:
        a, _, b = range_spec.partition(":")
        msgs = msgs[int(a):int(b) if b else None]

    return msgs


def filter_fragments(msg: dict, only: str) -> list[dict]:
    frags = msg.get("fragments", [])
    if only == "clean":
        return [f for f in frags if f.get("type") in ("REQUEST", "RESPONSE")]
    if only == "thinking":
        return [f for f in frags if f.get("type") == "THINK"]
    if only == "search":
        return [f for f in frags if f.get("type") in ("TOOL_SEARCH", "TOOL_OPEN")]
    if only == "tools":
        return [f for f in frags if (f.get("type") or "").startswith("TOOL_")]
    if only == "code":
        return [f for f in frags if "```" in (f.get("content") or "")]
    return frags
