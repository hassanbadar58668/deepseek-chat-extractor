import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table

from . import __version__
from .utils import ensure_dirs, OUT_DIR, ok, err, info
from . import fetcher, parser, extractor

app = typer.Typer(help="DeepSeek Chat Extractor CLI", add_completion=False)
console = Console()


@app.command()
def version():
    """إصدار الأداة."""
    console.print(f"dsx v{__version__}")


@app.command()
def fetch(
    value: str = typer.Argument(..., help="رابط المشاركة أو ID"),
    token: str = typer.Option(None, "--token", "-t", help="توكن للجلسات الخاصة"),
):
    """سحب محادثة وحفظها كـ JSON خام."""
    ensure_dirs()
    fetcher.fetch(value, token)


@app.command()
def parse(file: Path = typer.Argument(..., exists=True, help="ملف JSON خام")):
    """عرض بنية المحادثة."""
    data = parser.load(file)
    msgs = parser.get_messages(data)
    title = parser.get_title(data)
    console.print(f"[bold]📄 {title}[/bold]")
    console.print(f"عدد الرسائل: {len(msgs)}")

    users = sum(1 for m in msgs if m.get("role") == "USER")
    asst = sum(1 for m in msgs if m.get("role") == "ASSISTANT")

    # إحصاء أنواع fragments
    from collections import Counter
    types = Counter()
    for m in msgs:
        for f in m.get("fragments", []):
            types[f.get("type", "?")] += 1

    table = Table("الدور", "العدد")
    table.add_row("USER", str(users))
    table.add_row("ASSISTANT", str(asst))
    console.print(table)

    t2 = Table("نوع الـ fragment", "العدد")
    for t, c in types.most_common():
        t2.add_row(t, str(c))
    console.print(t2)


@app.command()
def extract(
    file: Path = typer.Argument(..., exists=True),
    only: str = typer.Option(
        "clean", "--only", "-o",
        help="clean|all|user|assistant|thinking|code|search|tools",
    ),
    last: int = typer.Option(None, "--last", "-n", help="آخر N رسالة"),
    range_: str = typer.Option(None, "--range", "-r", help="نطاق مثل 5:15"),
    keyword: str = typer.Option(None, "--keyword", "-k", help="بحث بكلمة"),
    fmt: str = typer.Option("md", "--format", "-f", help="md|txt|json"),
    out: Path = typer.Option(None, "--out", help="ملف الخروج"),
):
    """استخراج رسائل بفلاتر."""
    ensure_dirs()
    data = parser.load(file)
    msgs = extractor.filter_messages(data, only, last, range_, keyword)

    if out is None:
        out = OUT_DIR / f"{file.stem}_{only}.{fmt}"

    lines = []
    for m in msgs:
        role = m.get("role", "?")
        for frag in extractor.filter_fragments(m, only):
            t = frag.get("type", "TEXT")
            c = frag.get("content") or ""
            if fmt == "md":
                lines.append(f"## {role} [{t}]\n\n{c}\n\n---\n")
            elif fmt == "txt":
                lines.append(f"=== {role} [{t}] ===\n{c}\n")
            else:
                lines.append(c)

    out.write_text("\n".join(lines), encoding="utf-8")
    ok(f"تم الحفظ: {out}  ({len(msgs)} رسالة)")


@app.command()
def stats(file: Path = typer.Argument(..., exists=True)):
    """إحصائيات المحادثة."""
    data = parser.load(file)
    msgs = parser.get_messages(data)

    users = sum(1 for m in msgs if m.get("role") == "USER")
    asst = sum(1 for m in msgs if m.get("role") == "ASSISTANT")
    tokens = sum(m.get("accumulated_token_usage") or 0 for m in msgs)

    table = Table("المقياس", "القيمة")
    table.add_row("عنوان", parser.get_title(data))
    table.add_row("إجمالي الرسائل", str(len(msgs)))
    table.add_row("USER", str(users))
    table.add_row("ASSISTANT", str(asst))
    table.add_row("التوكنز", f"{tokens:,}")
    console.print(table)


if __name__ == "__main__":
    app()
