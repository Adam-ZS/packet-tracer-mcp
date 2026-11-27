"""Regression for Save As opening an overwrite modal and stalling the live bridge."""

import pytest

from packettracer_evidence_mcp.bridge import FileBridge
from packettracer_evidence_mcp.client import PacketTracer
from packettracer_evidence_mcp.config import Workspace


class SaveFixture(PacketTracer):
    def __init__(self, tmp_path, *, successful=True):
        super().__init__(FileBridge(tmp_path), Workspace(tmp_path))
        self.saved_path = tmp_path / "demo.pkt"
        self.saved_path.write_bytes(b"EXPLICIT TEST FIXTURE, NOT A PACKET TRACER FILE")
        self.calls = []
        self.successful = successful

    def _execute(self, body):
        self.calls.append(body)
        if "getSavedFilename" in body:
            return str(self.saved_path)
        if "fileSave()" in body:
            return self.successful
        raise AssertionError("Unexpected save path could open an overwrite modal")


def test_overwriting_current_project_uses_save_without_a_modal(tmp_path):
    client = SaveFixture(tmp_path)
    result = client.save("demo.pkt", overwrite=True)
    assert result["saved"]
    assert any("fileSave()" in code for code in client.calls)
    assert not any("fileSaveAs(" in code for code in client.calls)


def test_failed_native_save_is_not_reported_as_success(tmp_path):
    client = SaveFixture(tmp_path, successful=False)
    with pytest.raises(RuntimeError, match="did not confirm"):
        client.save("demo.pkt", overwrite=True)
