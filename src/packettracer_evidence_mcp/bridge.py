"""File mailbox transport compatible with Mats2208/MCP-Packet-Tracer.

The req_*.js / res_*.txt protocol and atomic publication pattern come from that
project. Its MIT notice is retained in THIRD_PARTY_NOTICES.md. No extension code
is bundled here.
"""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path
from uuid import uuid4


class BridgeUnavailable(RuntimeError):
    """Packet Tracer or its Control Center extension is not responding."""


class BridgeTimeout(TimeoutError):
    """A request timed out; its execution outcome may be unknown."""


class FileBridge:
    def __init__(self, directory: Path, *, poll_interval: float = 0.1):
        self.directory = directory
        self.poll_interval = poll_interval
        self.lock = threading.RLock()

    def heartbeat_age(self) -> float | None:
        try:
            return max(0, time.time() - (self.directory / "alive.txt").stat().st_mtime)
        except OSError:
            return None

    def alive(self) -> bool:
        age = self.heartbeat_age()
        return age is not None and age < 6

    def request(self, javascript: str, *, timeout: float = 20) -> str:
        if not 0 < timeout <= 120:
            raise ValueError("Bridge timeout must be between 0 and 120 seconds.")
        with self.lock:
            if not self.alive():
                raise BridgeUnavailable(
                    "No fresh Control Center heartbeat. Open Packet Tracer, install/enable the "
                    "upstream extension, and check PT_BRIDGE_DIR."
                )
            request_id = f"{os.getpid()}_{uuid4().hex}"
            request = self.directory / f"req_{request_id}.js"
            response = self.directory / f"res_{request_id}.txt"
            temporary = request.with_suffix(".tmp")
            try:
                # UTF-8 bytes avoid platform newline translation inside JavaScript strings.
                with temporary.open("xb") as stream:
                    stream.write(javascript.encode("utf-8"))
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, request)
                deadline = time.monotonic() + timeout
                while time.monotonic() < deadline:
                    if response.exists():
                        value = response.read_text(encoding="utf-8")
                        response.unlink(missing_ok=True)
                        return value
                    time.sleep(self.poll_interval)
                # Remove an unclaimed request. Execution may have started already: never retry.
                request.unlink(missing_ok=True)
                raise BridgeTimeout(
                    f"Request {request_id} timed out. Execution outcome is unknown. "
                    "Inspect Packet Tracer before repeating a mutation."
                )
            finally:
                temporary.unlink(missing_ok=True)
