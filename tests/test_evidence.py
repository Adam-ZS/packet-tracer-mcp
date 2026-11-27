"""Synthetic pixels below are test fixtures, not evidence from Packet Tracer."""

import json

import pytest
from PIL import Image

from packettracer_evidence_mcp.config import Workspace
from packettracer_evidence_mcp.evidence import capture, digest, verify


@pytest.fixture
def desktop_fixture(monkeypatch):
    image = Image.new("RGB", (32, 24))
    for y in range(24):
        for x in range(32):
            image.putpixel((x, y), (x * 7, y * 9, (x + y) * 4))
    monkeypatch.setattr("packettracer_evidence_mcp.evidence.ImageGrab.grab", lambda: image.copy())
    return image


def test_crop_pixels_and_hashes_are_exact(tmp_path, desktop_fixture):
    workspace = Workspace(tmp_path)
    record = capture(workspace, "TEST FIXTURE", [3, 4, 19, 16])
    cropped = Image.open(workspace.path(record["crop"]["path"]))
    assert cropped.tobytes() == desktop_fixture.crop((3, 4, 19, 16)).tobytes()
    result = verify(workspace, record["manifest"])
    assert result["integrity_ok"]
    assert result["attestation"] is False


def test_changed_pixels_fail_even_if_crop_hash_is_updated(tmp_path, desktop_fixture):
    workspace = Workspace(tmp_path)
    record = capture(workspace, "TEST FIXTURE")
    path = workspace.path(record["crop"]["path"])
    image = Image.open(path)
    image.putpixel((0, 0), (255, 0, 0))
    image.save(path)
    record["crop"]["sha256"] = digest(path)
    workspace.path(record["manifest"]).write_text(json.dumps(record))
    result = verify(workspace, record["manifest"])
    assert result["hashes_match"]
    assert not result["crop_pixels_match"]
    assert not result["integrity_ok"]


@pytest.mark.parametrize(
    "box", [[], [-1, 0, 5, 5], [0, 0, 40, 30], [1, 1, 1, 5], [0, 0, 5], [0, 0, 5.5, 8]]
)
def test_invalid_crop_never_writes_a_replacement(tmp_path, desktop_fixture, box):
    with pytest.raises(ValueError):
        capture(Workspace(tmp_path), "TEST FIXTURE", box)
    assert not list(tmp_path.rglob("*.png"))


def test_capture_failure_is_explicit(tmp_path, monkeypatch):
    def fail():
        raise OSError("No display")

    monkeypatch.setattr("packettracer_evidence_mcp.evidence.ImageGrab.grab", fail)
    with pytest.raises(RuntimeError, match="No image was generated"):
        capture(Workspace(tmp_path), "no display")
    assert not list(tmp_path.rglob("*.png"))


def test_manifest_cannot_read_outside_workspace(tmp_path, desktop_fixture):
    workspace = Workspace(tmp_path / "work")
    record = capture(workspace, "TEST FIXTURE")
    record["original"]["path"] = "../../outside.png"
    workspace.path(record["manifest"]).write_text(json.dumps(record))
    with pytest.raises(ValueError, match="escapes"):
        verify(workspace, record["manifest"])
