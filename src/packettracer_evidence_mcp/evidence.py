"""Capture original desktop pixels, crop them, and record integrity metadata."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageGrab

from .config import Workspace


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def capture(workspace: Workspace, label: str, box: list[int] | None = None) -> dict:
    """Always grab the real display. A capture failure never produces a replacement image."""
    try:
        original = ImageGrab.grab().convert("RGB")
    except Exception as error:
        raise RuntimeError(
            "Desktop capture failed. Use a supported logged-in desktop session "
            "(tested on Linux/X11). No image was generated."
        ) from error
    rectangle = tuple(box) if box is not None else (0, 0, original.width, original.height)
    if len(rectangle) != 4 or not all(type(v) is int for v in rectangle):
        raise ValueError("Crop must contain four integer coordinates: left, top, right, bottom.")
    left, top, right, bottom = rectangle
    if not (0 <= left < right <= original.width and 0 <= top < bottom <= original.height):
        raise ValueError(f"Crop is outside the {original.width}x{original.height} display.")
    timestamp = datetime.now(UTC)
    relative = f"evidence/{timestamp:%Y%m%dT%H%M%S}_{uuid4().hex[:12]}"
    raw = workspace.output(relative + "/original.png")
    cropped = workspace.output(relative + "/crop.png")
    manifest = workspace.output(relative + "/manifest.json")
    original.save(raw)
    original.crop(rectangle).save(cropped)
    record = {
        "schema_version": 1,
        "label": label,
        "captured_at": timestamp.isoformat(),
        "capture_method": "PIL.ImageGrab.grab",
        "processing": "crop only; no resampling, overlays or pixel replacement",
        "desktop_size": list(original.size),
        "crop_box": list(rectangle),
        "original": {"path": str(raw.relative_to(workspace.root)), "sha256": digest(raw)},
        "crop": {"path": str(cropped.relative_to(workspace.root)), "sha256": digest(cropped)},
        "manifest": str(manifest.relative_to(workspace.root)),
    }
    manifest.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return record


def verify(workspace: Workspace, manifest_path: str) -> dict:
    path = workspace.path(manifest_path, suffix=".json")
    record = json.loads(path.read_text(encoding="utf-8"))
    if record.get("schema_version") != 1:
        raise ValueError("Unsupported evidence manifest schema.")
    original_path = workspace.path(record["original"]["path"], suffix=".png")
    crop_path = workspace.path(record["crop"]["path"], suffix=".png")
    hashes_match = all(
        digest(p) == record[key]["sha256"]
        for p, key in [(original_path, "original"), (crop_path, "crop")]
    )
    with Image.open(original_path) as raw, Image.open(crop_path) as cropped:
        box = record["crop_box"]
        if len(box) != 4 or not all(type(v) is int for v in box):
            raise ValueError("Malformed crop box.")
        left, top, right, bottom = box
        valid = 0 <= left < right <= raw.width and 0 <= top < bottom <= raw.height
        expected = raw.crop(box).convert("RGB") if valid else None
        pixels_match = (
            expected is not None
            and expected.size == cropped.size
            and expected.tobytes() == cropped.convert("RGB").tobytes()
        )
        size_matches = list(raw.size) == record["desktop_size"]
    return {
        "integrity_ok": hashes_match and pixels_match and size_matches,
        "hashes_match": hashes_match,
        "crop_pixels_match": pixels_match,
        "desktop_size_matches": size_matches,
        "attestation": False,
        "note": "Integrity checks detect changes relative to the manifest, not trusted origin.",
    }
