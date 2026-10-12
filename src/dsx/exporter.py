import csv
import html
import json
import datetime
from pathlib import Path
from .parser import get_messages, get_title
from .extractor import filter_fragments
from .utils import ok, info


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
body {{ font-family: -apple-system, "Segoe UI", Tahoma, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; line-height: 1.7; background: #fafafa; color: #222; }}
h1 {{ border-bottom: 3px solid #4a90e2; padding-bottom: .5rem; }}
.msg {{ margin: 1.5rem 0; padding: 1rem 1.2rem; border-radius: 10px; box-shadow: 0 1px 4px rgba(0,0,0,.06); }}
.USER {{ background: #e3f2fd; border-right: 4px solid #1976d2; }}
.ASSISTANT {{ background: #f1f8e9; border-right: 4px solid #689f38; }}
.role {{ font-weight: bold; font-size: .95rem; opacity: .75; margin-bottom: .5rem; }}
.type {{ background: #eee; padding: .15rem .5rem; border-radius: 4px; font-size: .8rem; margin-left: .5rem; }}
pre {{ background: #2d2d2d; color: #f8f8f2; padding: 1rem; border-radius: 6px; overflow-x: auto; direction: ltr; text-align: left; }}
code {{ background: #eee; padding: .1rem .3rem; border-radius: 3px; font-family: monospace; direction: ltr; display: inline-block; }}
pre code {{ background: none; padding: 0; color: inherit; }}
.meta {{ color: #888; font-size: .85rem; text-align: center; margin: 2rem 0; }}
hr {{ border: none; border-top: 1px solid #ddd; margin: 2rem 0; }}
</style>
</head>
<body>
<h1>📄 {title}</h1>
<p class="meta">عدد الرسائل: {count} — تاريخ التصدير: {date}</p>
<hr>
{body}
</body>
</html>
"""


def _md_to_html_basic(text: str) -> str:
    import re
    def code_block(m):
        code = html.escape(m.group(2))
        return f"<pre><code>{code}</code></pre>"
    text = re.sub(r"```(\w+)?\n(.*?)```", code_block, text, flags=re.DOTALL)
    text = re.sub(r"`([^`]+)`", lambda m: f"<code>{html.escape(m.group(1))}</code>", text)
    for i in range(6, 0, -1):
        text = re.sub(rf"^{'#' * i} (.+)$", rf"<h{i}>\1</h{i}>", text, flags=re.MULTILINE)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    text = text.replace("\n\n", "</p><p>")
    text = f"<p>{text}</p>"
    return text


def export_html(data: dict, out: Path, only: str = "clean") -> Path:
    msgs = get_messages(data)
    title = get_title(data)
    body_parts = []
    for m in msgs:
        role = m.get("role", "?")
        for frag in filter_fragments(m, only):
            t = frag.get("type", "TEXT")
            c = frag.get("content") or ""
            html_content = _md_to_html_basic(c)
            body_parts.append(
                f'<div class="msg {role}">'
                f'<div class="role">{role}<span class="type">{t}</span></div>'
                f'{html_content}</div>'
            )
    content = HTML_TEMPLATE.format(
        title=html.escape(title),
        count=len(msgs),
        date=datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        body="\n".join(body_parts),
    )
    out.write_text(content, encoding="utf-8")
    return out


def export_csv(data: dict, out: Path, only: str = "clean") -> Path:
    msgs = get_messages(data)
    with out.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["#", "role", "type", "tokens", "chars", "content"])
        for i, m in enumerate(msgs):
            role = m.get("role", "?")
            tokens = m.get("accumulated_token_usage") or 0
            for frag in filter_fragments(m, only):
                t = frag.get("type", "TEXT")
                c = (frag.get("content") or "").replace("\n", " ")
                w.writerow([i, role, t, tokens, len(c), c[:500]])
    return out


def export_plain_json(data: dict, out: Path, only: str = "clean") -> Path:
    msgs = get_messages(data)
    out_msgs = []
    for m in msgs:
        frags = filter_fragments(m, only)
        if not frags:
            continue
        out_msgs.append({
            "role": m.get("role"),
            "inserted_at": m.get("inserted_at"),
            "tokens": m.get("accumulated_token_usage"),
            "fragments": [{"type": f.get("type"), "content": f.get("content")} for f in frags],
        })
    out.write_text(json.dumps(out_msgs, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
