from pathlib import Path
from .utils import RAW_DIR, OUT_DIR, ok, err, info, warn


def merge_files(input_dir: Path, out_file: Path, pattern: str = "*.md") -> Path:
    """يدمج ملفات مقسمة لملف واحد بالترتيب."""
    files = sorted(input_dir.glob(pattern))
    if not files:
        err(f"مفيش ملفات بـ {pattern} في {input_dir}")
        return out_file

    parts = []
    for f in files:
        parts.append(f.read_text(encoding="utf-8"))

    out_file.write_text("\n\n".join(parts), encoding="utf-8")
    return out_file


def diff_two_files(a: Path, b: Path) -> dict:
    """يقارن ملفين ويُرجع فرق أساسي."""
    ta = a.read_text(encoding="utf-8", errors="ignore").splitlines()
    tb = b.read_text(encoding="utf-8", errors="ignore").splitlines()

    set_a = set(ta)
    set_b = set(tb)

    only_a = [l for l in ta if l not in set_b]
    only_b = [l for l in tb if l not in set_a]

    return {
        "lines_a": len(ta),
        "lines_b": len(tb),
        "unique_a": len(only_a),
        "unique_b": len(only_b),
        "only_a": only_a[:20],
        "only_b": only_b[:20],
    }


def clean_temp(min_size_kb: int = 0) -> int:
    """يحذف الملفات المؤقتة (.tmp) ويمكن يحذف الصغيرة."""
    count = 0
    for d in (RAW_DIR, OUT_DIR):
        if not d.exists():
            continue
        for f in d.rglob("*.tmp"):
            f.unlink()
            count += 1
        for f in d.rglob(".tmp_*"):
            f.unlink()
            count += 1
    return count


def find_all_raw() -> list[Path]:
    """كل ملفات JSON الخام."""
    if not RAW_DIR.exists():
        return []
    return sorted(RAW_DIR.glob("*.json"))
