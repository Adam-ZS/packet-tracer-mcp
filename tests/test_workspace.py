from pathlib import Path

import pytest

from packettracer_evidence_mcp.config import Workspace, discover_bridge


@pytest.mark.parametrize("path", ["../outside.pkt", "/tmp/outside.pkt", "", "sub/../../outside"])
def test_output_paths_stay_in_workspace(tmp_path, path):
    with pytest.raises(ValueError):
        Workspace(tmp_path / "work").output(path)


def test_symlink_escape_and_existing_outputs(tmp_path):
    work = tmp_path / "work"
    work.mkdir()
    (work / "escape").symlink_to(tmp_path, target_is_directory=True)
    workspace = Workspace(work)
    with pytest.raises(ValueError):
        workspace.output("escape/secret.txt")
    path = workspace.output("saved/demo.pkt", suffix=".pkt")
    path.write_bytes(b"fixture")
    with pytest.raises(FileExistsError):
        workspace.output("saved/demo.pkt", suffix=".pkt")
    assert workspace.output("saved/demo.pkt", suffix=".pkt", overwrite=True) == path
    with pytest.raises(ValueError):
        workspace.output("saved/demo.txt", suffix=".pkt")


def test_bridge_override_is_explicit(tmp_path, monkeypatch):
    monkeypatch.setenv("PT_BRIDGE_DIR", str(tmp_path / "chosen"))
    assert discover_bridge() == tmp_path / "chosen"


def test_discovery_prefers_most_recent_heartbeat(tmp_path, monkeypatch):
    import os

    monkeypatch.delenv("PT_BRIDGE_DIR", raising=False)
    monkeypatch.delenv("LOCALAPPDATA", raising=False)
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    old = tmp_path / "state/packet-tracer-mcp/bridge/alive.txt"
    new = tmp_path / "AppData/Local/packet-tracer-mcp/bridge/alive.txt"
    for path in [old, new]:
        path.parent.mkdir(parents=True)
        path.touch()
    os.utime(old, (1, 1))
    assert discover_bridge() == new.parent
