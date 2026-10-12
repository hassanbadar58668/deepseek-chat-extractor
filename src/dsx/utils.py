from pathlib import Path
from rich.console import Console

console = Console()

DEFAULT_DIR = Path.home() / "dsx_data"
RAW_DIR = DEFAULT_DIR / "raw"
OUT_DIR = DEFAULT_DIR / "output"


def ensure_dirs():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)


def ok(msg: str):
    console.print(f"[green]✅ {msg}[/green]")


def warn(msg: str):
    console.print(f"[yellow]⚠️  {msg}[/yellow]")


def err(msg: str):
    console.print(f"[red]❌ {msg}[/red]")


def info(msg: str):
    console.print(f"[cyan]ℹ️  {msg}[/cyan]")
