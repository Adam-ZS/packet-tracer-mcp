import os
import sys

import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_real_stdio_handshake_tools_and_offline_error_recovery(tmp_path):
    env = dict(os.environ)
    env.update(
        {
            "PT_WORKSPACE": str(tmp_path / "work"),
            "PT_BRIDGE_DIR": str(tmp_path / "offline"),
            "PT_ENABLE_DESKTOP": "0",
        }
    )
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "packettracer_evidence_mcp.cli", "serve"],
        env=env,
    )
    async with stdio_client(params) as (reader, writer), ClientSession(reader, writer) as session:
        await session.initialize()
        listed = await session.list_tools()
        names = {tool.name for tool in listed.tools}
        assert len(names) == 21
        assert {"pt_terminal", "pt_capture", "pt_fill_report"} <= names
        assert "pt_desktop_action" not in names
        status = await session.call_tool("pt_status", {})
        assert status.structuredContent["extension_alive"] is False
        failed = await session.call_tool("pt_devices", {})
        assert failed.isError
        assert not (await session.call_tool("pt_status", {})).isError
        assert len((await session.list_resources()).resources) == 1
        assert (await session.list_prompts()).prompts[0].name == "record_lab"
