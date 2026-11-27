"""Local configuration and output path boundaries."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def discover_bridge() -> Path:
    """Find the installed Control Center mailbox without creating external directories."""
    if value := os.getenv("PT_BRIDGE_DIR"):
        return Path(value).expanduser().resolve()
    home = Path.home()
    candidates = [
        Path(os.getenv("XDG_STATE_HOME", str(home / ".local/state"))) / "packet-tracer-mcp/bridge",
        home / "AppData/Local/packet-tracer-mcp/bridge",
        home / ".packet-tracer-mcp/bridge",
    ]
    if value := os.getenv("LOCALAPPDATA"):
        candidates.insert(0, Path(value) / "packet-tracer-mcp/bridge")
    existing = [p for p in candidates if (p / "alive.txt").is_file()]
    return (
        max(existing, key=lambda p: (p / "alive.txt").stat().st_mtime)
        if existing
        else candidates[0]
    ).resolve()


@dataclass(frozen=True)
class Settings:
    bridge_dir: Path
    workspace: Path

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            discover_bridge(),
            Path(os.getenv("PT_WORKSPACE", str(Path.cwd() / "workspace"))).expanduser().resolve(),
        )


class Workspace:
    """Keep generated files under the configured root, including through symlinks."""

    def __init__(self, root: Path):
        self.root = root.expanduser().resolve()

    def path(self, relative: str, *, suffix: str | None = None) -> Path:
        if not relative or Path(relative).is_absolute():
            raise ValueError("Use a nonempty path relative to PT_WORKSPACE.")
        target = (self.root / relative).resolve()
        if target == self.root or not target.is_relative_to(self.root):
            raise ValueError("Path escapes PT_WORKSPACE.")
        if suffix and target.suffix.lower() != suffix:
            raise ValueError(f"Expected a {suffix} file.")
        return target

    def output(self, relative: str, *, suffix: str | None = None, overwrite: bool = False) -> Path:
        target = self.path(relative, suffix=suffix)
        if target.exists() and not overwrite:
            raise FileExistsError(f"Output already exists: {relative}")
        target.parent.mkdir(parents=True, exist_ok=True)
        return target
