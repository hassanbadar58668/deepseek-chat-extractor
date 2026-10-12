import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table

from . import __version__
from .utils import ensure_dirs, OUT_DIR, ok, err, info
from . import fetcher, parser, extractor, splitter, analyzer, backup

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
    upload: bool = typer.Option(False, "--upload", "-u", help="ارفع لـ Koofr تلقائياً"),
    remote: str = typer.Option("koofr-dsx:dsx_backup/raw", "--remote"),
):
    """سحب محادثة وحفظها كـ JSON خام."""
    ensure_dirs()
    out = fetcher.fetch(value, token)
    if upload:
        backup.upload(out, remote)


@app.command()
def parse(file: Path = typer.Argument(..., exists=True)):
    """عرض بنية المحادثة."""
    from collections import Counter
    data = parser.load(file)
    msgs = parser.get_messages(data)
    title = parser.get_title(data)
    console.print(f"[bold]📄 {title}[/bold]")
    console.print(f"عدد الرسائل: {len(msgs)}")

    users = sum(1 for m in msgs if m.get("role") == "USER")
    asst = sum(1 for m in msgs if m.get("role") == "ASSISTANT")

    table = Table("الدور", "العدد")
    table.add_row("USER", str(users))
    table.add_row("ASSISTANT", str(asst))
    console.print(table)

    types = Counter()
    for m in msgs:
        for f in m.get("fragments", []):
            types[f.get("type", "?")] += 1

    t2 = Table("نوع الـ fragment", "العدد")
    for t, c in types.most_common():
        t2.add_row(t, str(c))
    console.print(t2)


@app.command()
def extract(
    file: Path = typer.Argument(..., exists=True),
    only: str = typer.Option("clean", "--only", "-o",
        help="clean|all|user|assistant|thinking|code|search|tools"),
    last: int = typer.Option(None, "--last", "-n"),
    range_: str = typer.Option(None, "--range", "-r"),
    keyword: str = typer.Option(None, "--keyword", "-k"),
    fmt: str = typer.Option("md", "--format", "-f"),
    out: Path = typer.Option(None, "--out"),
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


@app.command()
def split(
    file: Path = typer.Argument(..., exists=True),
    by_messages: int = typer.Option(None, "--by-messages", "-m"),
    by_size: float = typer.Option(None, "--by-size", "-s"),
    only: str = typer.Option("clean", "--only", "-o"),
    fmt: str = typer.Option("md", "--format", "-f"),
    out_dir: Path = typer.Option(None, "--out-dir"),
):
    """تقسيم محادثة ضخمة لملفات أصغر."""
    ensure_dirs()
    if not by_messages and not by_size:
        err("حدد --by-messages أو --by-size")
        raise SystemExit(1)
    data = parser.load(file)
    if out_dir is None:
        out_dir = OUT_DIR / f"{file.stem}_parts"
    if by_messages:
        files = splitter.split_by_messages(data, out_dir, by_messages, only, fmt)
    else:
        files = splitter.split_by_size(data, out_dir, by_size, only, fmt)
    ok(f"تم التقسيم: {len(files)} ملف في {out_dir}")


@app.command()
def paths(file: Path = typer.Argument(..., exists=True)):
    """استخراج مسارات الملفات."""
    data = parser.load(file)
    ps = analyzer.extract_paths(data)
    out = OUT_DIR / f"{file.stem}_paths.txt"
    out.write_text("\n".join(ps), encoding="utf-8")
    ok(f"تم الحفظ: {out} ({len(ps)} مسار)")
    for p in ps[:20]:
        console.print(f"  • {p}")
    if len(ps) > 20:
        info(f"... و {len(ps) - 20} مسار آخر")


@app.command()
def tree(file: Path = typer.Argument(..., exists=True)):
    """استخراج شجرة المشروع."""
    data = parser.load(file)
    lines = analyzer.extract_tree(data)
    out = OUT_DIR / f"{file.stem}_tree.txt"
    out.write_text("\n".join(lines), encoding="utf-8")
    ok(f"تم الحفظ: {out} ({len(lines)} سطر)")
    for line in lines[:30]:
        console.print(line)
    if len(lines) > 30:
        info(f"... و {len(lines) - 30} سطر آخر")


@app.command()
def keywords(
    file: Path = typer.Argument(..., exists=True),
    top: int = typer.Option(30, "--top", "-t"),
):
    """أكثر الكلمات تكرارًا."""
    data = parser.load(file)
    kws = analyzer.extract_keywords(data, top)
    table = Table("الكلمة", "التكرار")
    for w, c in kws:
        table.add_row(w, str(c))
    console.print(table)


@app.command()
def search(
    file: Path = typer.Argument(..., exists=True),
    keyword: str = typer.Argument(...),
):
    """بحث بكلمة في محادثة."""
    data = parser.load(file)
    hits = analyzer.search_in_messages(data, keyword)
    console.print(f"[bold]نتائج البحث عن:[/bold] {keyword}  ({len(hits)} نتيجة)")
    for i, role, snippet in hits[:30]:
        console.print(f"[cyan]#{i}[/cyan] [{role}] {snippet}")
    if len(hits) > 30:
        info(f"... و {len(hits) - 30} نتيجة أخرى")


# ============ أوامر Koofr / rclone ============

backup_app = typer.Typer(help="رفع/تنزيل/مزامنة مع Koofr عبر rclone")
app.add_typer(backup_app, name="backup")


@backup_app.command("check")
def backup_check(remote: str = typer.Option("koofr-dsx", "--remote", "-r")):
    """يتأكد إن الـ remote متظبط."""
    if backup.is_configured(remote):
        ok(f"rclone متظبط مع: {remote}")
    else:
        err(f"مش لاقي remote اسمه: {remote}")
        info("شغل: rclone config")


@backup_app.command("ls")
def backup_ls(remote: str = typer.Option("koofr-dsx:dsx_backup", "--remote", "-r")):
    """يعرض الملفات على Koofr."""
    files = backup.list_files(remote)
    if not files:
        info("المجلد فاضي")
        return
    for f in files:
        console.print(f"  • {f}")


@backup_app.command("upload")
def backup_upload(
    path: Path = typer.Argument(...),
    remote: str = typer.Option("koofr-dsx:dsx_backup", "--remote", "-r"),
    dry: bool = typer.Option(False, "--dry-run"),
):
    """رفع ملف/مجلد محدد."""
    backup.upload(path, remote, dry_run=dry)


@backup_app.command("sync")
def backup_sync(
    remote: str = typer.Option("koofr-dsx:dsx_backup", "--remote", "-r"),
    dry: bool = typer.Option(False, "--dry-run"),
):
    """مزامنة dsx_data كاملة."""
    backup.sync_all(remote, dry_run=dry)


@backup_app.command("push-output")
def backup_push_output(
    remote: str = typer.Option("koofr-dsx:dsx_backup/output", "--remote", "-r"),
    dry: bool = typer.Option(False, "--dry-run"),
):
    """رفع مجلد المخرجات."""
    backup.upload_output(remote, dry_run=dry)


@backup_app.command("push-raw")
def backup_push_raw(
    remote: str = typer.Option("koofr-dsx:dsx_backup/raw", "--remote", "-r"),
    dry: bool = typer.Option(False, "--dry-run"),
):
    """رفع JSON الخام."""
    backup.upload_raw(remote, dry_run=dry)


@backup_app.command("pull")
def backup_pull(
    remote_path: str = typer.Argument(...),
    local: Path = typer.Argument(...),
    remote: str = typer.Option("koofr-dsx:dsx_backup", "--remote", "-r"),
):
    """تنزيل من Koofr."""
    backup.download(remote_path, local, remote)


if __name__ == "__main__":
    app()
