from pathlib import Path
from .parser import get_messages, get_title
from .extractor import filter_fragments
from .utils import OUT_DIR, ok, info


def split_by_messages(
    data: dict,
    out_dir: Path,
    chunk_size: int = 50,
    only: str = "clean",
    fmt: str = "md",
) -> list[Path]:
    msgs = get_messages(data)
    title = get_title(data)
    out_dir.mkdir(parents=True, exist_ok=True)

    files = []
    total_chunks = (len(msgs) + chunk_size - 1) // chunk_size

    for i in range(0, len(msgs), chunk_size):
        chunk = msgs[i:i + chunk_size]
        idx = i // chunk_size + 1
        out = out_dir / f"{title}_{idx:03d}_of_{total_chunks:03d}.{fmt}"

        lines = [f"# {title} — جزء {idx}/{total_chunks}\n\n"]
        for m in chunk:
            role = m.get("role", "?")
            for frag in filter_fragments(m, only):
                t = frag.get("type", "TEXT")
                c = frag.get("content") or ""
                if fmt == "md":
                    lines.append(f"## {role} [{t}]\n\n{c}\n\n---\n")
                else:
                    lines.append(f"=== {role} [{t}] ===\n{c}\n")

        out.write_text("\n".join(lines), encoding="utf-8")
        files.append(out)

    return files


def split_by_size(
    data: dict,
    out_dir: Path,
    max_mb: float = 1.0,
    only: str = "clean",
    fmt: str = "md",
) -> list[Path]:
    msgs = get_messages(data)
    title = get_title(data)
    out_dir.mkdir(parents=True, exist_ok=True)
    max_bytes = int(max_mb * 1024 * 1024)

    files = []
    buf = []
    buf_size = 0
    idx = 1

    def flush():
        nonlocal buf, buf_size, idx
        if not buf:
            return
        out = out_dir / f"{title}_part{idx:03d}.{fmt}"
        out.write_text("\n".join(buf), encoding="utf-8")
        files.append(out)
        buf = []
        buf_size = 0
        idx += 1

    header = f"# {title}\n\n"
    buf.append(header)
    buf_size += len(header.encode("utf-8"))

    for m in msgs:
        role = m.get("role", "?")
        for frag in filter_fragments(m, only):
            t = frag.get("type", "TEXT")
            c = frag.get("content") or ""
            if fmt == "md":
                block = f"## {role} [{t}]\n\n{c}\n\n---\n"
            else:
                block = f"=== {role} [{t}] ===\n{c}\n"
            b = len(block.encode("utf-8"))
            if buf_size + b > max_bytes and len(buf) > 1:
                flush()
                buf.append(header)
                buf_size = len(header.encode("utf-8"))
            buf.append(block)
            buf_size += b

    flush()
    return files
