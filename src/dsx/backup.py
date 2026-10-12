import subprocess
from pathlib import Path
from .utils import DEFAULT_DIR, ok, err, info


def _run(cmd: list[str]) -> tuple[int, str, str]:
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def is_configured(remote: str = "koofr-dsx") -> bool:
    code, out, _ = _run(["rclone", "listremotes"])
    return code == 0 and f"{remote}:" in out


def list_files(remote: str = "koofr-dsx:dsx_backup") -> list[str]:
    code, out, err_ = _run(["rclone", "lsf", remote, "--max-depth", "1"])
    if code != 0:
        err(f"فشل: {err_}")
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def upload(source: Path, remote: str = "koofr-dsx:dsx_backup", dry_run: bool = False) -> bool:
    if not source.exists():
        err(f"مش موجود: {source}")
        return False
    cmd = ["rclone", "copy", str(source), remote, "--progress"]
    if dry_run:
        cmd.append("--dry-run")
    info(f"⬆️  رفع: {source} → {remote}")
    code, _, err_ = _run(cmd)
    if code != 0:
        err(f"فشل الرفع: {err_}")
        return False
    ok("تم الرفع")
    return True


def upload_output(remote: str = "koofr-dsx:dsx_backup/output", dry_run: bool = False) -> bool:
    from .utils import OUT_DIR
    return upload(OUT_DIR, remote, dry_run)


def upload_raw(remote: str = "koofr-dsx:dsx_backup/raw", dry_run: bool = False) -> bool:
    from .utils import RAW_DIR
    return upload(RAW_DIR, remote, dry_run)


def sync_all(remote: str = "koofr-dsx:dsx_backup", dry_run: bool = False) -> bool:
    return upload(DEFAULT_DIR, remote, dry_run)


def download(remote_path: str, local: Path, remote: str = "koofr-dsx:dsx_backup") -> bool:
    full = f"{remote}/{remote_path}"
    info(f"⬇️  تنزيل: {full} → {local}")
    cmd = ["rclone", "copy", full, str(local), "--progress"]
    code, _, err_ = _run(cmd)
    if code != 0:
        err(f"فشل التنزيل: {err_}")
        return False
    ok("تم التنزيل")
    return True
