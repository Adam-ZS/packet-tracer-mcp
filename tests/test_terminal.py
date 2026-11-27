from packettracer_evidence_mcp.bridge import FileBridge
from packettracer_evidence_mcp.client import PacketTracer
from packettracer_evidence_mcp.config import Workspace
from packettracer_evidence_mcp.redaction import Redactor


class ConsoleFixture(PacketTracer):
    def __init__(self, tmp_path, snapshots):
        super().__init__(FileBridge(tmp_path), Workspace(tmp_path))
        self.snapshots = iter(snapshots)
        self.reads = 0

    def snapshot(self, name):
        self.reads += 1
        return {"output": next(self.snapshots), "prompt": "R1#"}

    def _execute(self, body):
        return True


def test_old_prompt_does_not_satisfy_a_new_command(tmp_path):
    client = ConsoleFixture(
        tmp_path, ["R1#", "R1#\nR1#ping 192.0.2.2", "R1#\nSuccess rate 100%\nR1#"]
    )
    result = client.terminal("R1", "ping 192.0.2.2", r"R1#")
    assert client.reads == 3
    assert result["matched"]
    assert "Success rate 100%" in result["new_output"]


def test_password_input_is_not_returned_in_text(tmp_path):
    client = ConsoleFixture(tmp_path, ["Password:", "Password:\nlab-pass-123\nR1>"])
    result = client.terminal("R1", "lab-pass-123", r"R1>\s*$", secret=True)
    assert result["matched"]
    assert "lab-pass-123" not in result["new_output"]
    assert "[REDACTED]" in result["new_output"]


def test_ios_credentials_and_registered_secrets_are_redacted():
    redactor = Redactor()
    redactor.remember("a-shared-secret")
    text = (
        "username admin secret 5 HASH\n password 7 HASH\n"
        "radius-server key RADIUSKEY\nvalue a-shared-secret"
    )
    actual = redactor.filter(text)
    assert "HASH" not in actual and "RADIUSKEY" not in actual and "a-shared-secret" not in actual
    assert "username admin secret" in actual
