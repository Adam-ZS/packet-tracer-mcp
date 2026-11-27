"""Protocol tests use a fake mailbox worker, never simulated screenshot evidence."""

import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest

from packettracer_evidence_mcp.bridge import BridgeTimeout, BridgeUnavailable, FileBridge


def worker(directory, count):
    received = []

    def run():
        deadline = time.monotonic() + 3
        while len(received) < count and time.monotonic() < deadline:
            for request in directory.glob("req_*.js"):
                data = request.read_bytes()
                received.append((request.name, data))
                response = directory / ("res_" + request.stem[4:] + ".txt")
                request.unlink()
                response.write_bytes(data)
            time.sleep(0.002)

    thread = threading.Thread(target=run)
    thread.start()
    return thread, received


def test_atomic_utf8_and_unique_request_ids(tmp_path):
    (tmp_path / "alive.txt").touch()
    thread, received = worker(tmp_path, 2)
    first, second = (
        FileBridge(tmp_path, poll_interval=0.002),
        FileBridge(tmp_path, poll_interval=0.002),
    )
    payloads = ['reportResult("\\n\\r\\t café");', 'reportResult("second");']
    with ThreadPoolExecutor(2) as pool:
        results = list(
            pool.map(
                lambda args: args[0].request(args[1]), zip([first, second], payloads, strict=True)
            )
        )
    thread.join(timeout=3)
    assert results == payloads
    assert len({name for name, _ in received}) == 2
    assert {data for _, data in received} == {p.encode("utf-8") for p in payloads}
    assert not list(tmp_path.glob("*.tmp"))
    assert not list(tmp_path.glob("res_*.txt"))


def test_stale_heartbeat_does_not_queue_commands(tmp_path):
    heartbeat = tmp_path / "alive.txt"
    heartbeat.touch()
    os.utime(heartbeat, (time.time() - 60, time.time() - 60))
    with pytest.raises(BridgeUnavailable):
        FileBridge(tmp_path).request("mutation")
    assert not list(tmp_path.glob("req_*.js"))


def test_timeout_is_not_retried_and_does_not_delete_other_requests(tmp_path):
    (tmp_path / "alive.txt").touch()
    unrelated = tmp_path / "req_other.js"
    unrelated.write_text("other")
    with pytest.raises(BridgeTimeout, match="outcome is unknown"):
        FileBridge(tmp_path, poll_interval=0.002).request("mutation", timeout=0.02)
    assert list(tmp_path.glob("req_*.js")) == [unrelated]


def test_missing_bridge_is_not_created(tmp_path):
    path = tmp_path / "absent"
    with pytest.raises(BridgeUnavailable):
        FileBridge(path).request("read")
    assert not path.exists()
