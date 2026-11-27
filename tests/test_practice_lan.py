from unittest.mock import Mock

import pytest

from packettracer_evidence_mcp.bridge import FileBridge
from packettracer_evidence_mcp.client import PacketTracer
from packettracer_evidence_mcp.config import Workspace


@pytest.fixture
def tracer(tmp_path):
    client = PacketTracer(FileBridge(tmp_path), Workspace(tmp_path))
    client.devices = Mock(return_value=[])
    client._execute = Mock()
    client.pc_ip = Mock()
    client.configure_ios = Mock(return_value={"detected_errors": []})
    client.save = Mock(return_value={"saved": True, "path": "demo.pkt"})
    return client


def test_existing_topology_is_left_alone(tracer):
    tracer.devices.return_value = [{"model": "PC-PT"}]
    with pytest.raises(ValueError, match="blank Packet Tracer project"):
        tracer.build_practice_lan("demo.pkt")
    tracer._execute.assert_not_called()


def test_existing_output_is_rejected_before_device_changes(tracer, tmp_path):
    (tmp_path / "demo.pkt").touch()
    with pytest.raises(FileExistsError):
        tracer.build_practice_lan("demo.pkt")
    tracer._execute.assert_not_called()


def test_server_timeout_does_not_save_a_verified_project(tracer):
    tracer.terminal = Mock(
        side_effect=[
            {"matched": True, "timed_out": False, "new_output": "Lost = 0 (0% loss)"},
            {"matched": False, "timed_out": True, "new_output": ""},
        ]
    )
    result = tracer.build_practice_lan("demo.pkt")
    assert result["checks"][0]["passed"]
    assert not result["checks"][1]["passed"]
    assert not result["verified"]
    assert not result["saved"]
    tracer.save.assert_not_called()
