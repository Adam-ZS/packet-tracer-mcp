"""MCP stdio server. No generated terminal images and no arbitrary-JavaScript tool."""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from functools import partial
from typing import Any, Literal

from anyio import to_thread
from mcp.server.fastmcp import FastMCP, Image
from mcp.types import ImageContent, TextContent, ToolAnnotations

from .client import PacketTracer
from .evidence import capture, verify
from .reports import fill_report

READ = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False)
WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, openWorldHint=False)
DESTRUCTIVE = ToolAnnotations(readOnlyHint=False, destructiveHint=True, openWorldHint=False)

WORKFLOW = r"""Build and verify networks in the user's running Cisco Packet Tracer application.
1. Call pt_status and pt_devices. If the extension is offline, resolve setup before editing.
2. For a starter router, switch, PC and server LAN, use pt_build_practice_lan on a blank canvas.
   It creates real devices and cables, sets addresses, tests both PC pings and saves on success.
3. For a custom topology, place each device with pt_add_device(name, model, x, y).
   Use models 2911, ISR4331, 2960-24TT, PC-PT and Server-PT as appropriate.
   Call pt_devices again and copy full port names. A 2911 uses GigabitEthernet0/0.
   An ISR4331 uses GigabitEthernet0/0/0. PCs and servers usually use FastEthernet0.
4. Use pt_connect(a, a_port, b, b_port, cable="straight") to create an actual Ethernet link.
   Use a different switch port for every link, for example FastEthernet0/1, 0/2 and 0/3.
   Use pt_move_device and pt_add_note for layout and labels after creating the links.
5. Set PC and Server-PT addressing with pt_pc_ip(device, address, mask, gateway).
   Set router interfaces and routes with pt_configure_ios. Include no shutdown on used ports.
   Configure switch VLANs and its management SVI with IOS when the lab calls for them.
6. Use pt_terminal to run pings and IOS show commands. For PC pings use C:\\>\s*$.
   On a fresh IOS console answer no to initial setup if prompted, then send a blank command
   at Press RETURN to get started and use enable. Read the new output and actual prompt.
   For login and RSA prompts send one answer per call. Recheck addressing, link state,
   VLANs, routing and ARP when a ping fails. Verify results from output and ping statistics.
7. Use pt_radius_setup for a simulated Server-PT AAA service. Match client IP, auth port
   and shared secret to the router. Test authentication only after verifying connectivity.
8. For evidence, focus the live window and capture its real pixels with pt_capture.
   Verify the manifest and use pt_fill_report for explicit placeholders in a DOCX copy.
9. Save the real .pkt under PT_WORKSPACE. Reopen only when authorized to replace the canvas.
Keep IDs, credentials and unrelated desktop content out of public examples.
"""


async def invoke(function, *args, **kwargs):
    return await to_thread.run_sync(partial(function, *args, **kwargs))


def create_server(client: PacketTracer) -> FastMCP:
    mcp = FastMCP(
        "Packet Tracer MCP",
        instructions=WORKFLOW,
        website_url="https://github.com/Adam-ZS/packet-tracer-mcp",
    )

    @mcp.tool(annotations=READ)
    def pt_status() -> dict[str, Any]:
        """Check the local extension heartbeat and configured workspace without modifying PT."""
        return client.status()

    @mcp.tool(annotations=READ)
    async def pt_devices() -> list[dict[str, Any]]:
        """Inspect actual device names, models, ports and canvas coordinates in the live project."""
        return await invoke(client.devices)

    @mcp.tool(annotations=DESTRUCTIVE)
    async def pt_new_project(confirm_discard: bool = False) -> dict[str, Any]:
        """Start a new project, explicitly discarding current unsaved work."""
        return await invoke(client.new, confirm_discard)

    @mcp.tool(annotations=WRITE)
    async def pt_build_practice_lan(output: str = "practice-lan.pkt") -> dict[str, Any]:
        """Build a four-device LAN in a blank project, test both PC pings and save a .pkt.

        Creates a 2911, 2960, PC-PT and Server-PT with three links and static addresses.
        The output path must be new and relative to PT_WORKSPACE. Allow time for both pings.
        On a failed ping the topology stays on the canvas for inspection.
        """
        return await invoke(client.build_practice_lan, output)

    @mcp.tool(annotations=WRITE)
    async def pt_project_info(
        name: str, description: str, additional_info: str = ""
    ) -> dict[str, Any]:
        """Set project name and description, clearing the profile email."""
        return await invoke(client.project_info, name, description, additional_info)

    @mcp.tool(annotations=WRITE)
    async def pt_add_device(
        name: str,
        model: Literal["2911", "ISR4331", "2960-24TT", "PC-PT", "Server-PT"],
        x: int,
        y: int,
    ) -> dict[str, Any]:
        """Create a supported live device. Use ISR4331, not 4331, for that model."""
        return await invoke(client.add_device, name, model, x, y)

    @mcp.tool(annotations=WRITE)
    async def pt_connect(
        a: str,
        a_port: str,
        b: str,
        b_port: str,
        cable: Literal["straight", "crossover", "serial"] = "straight",
    ) -> dict[str, Any]:
        """Create an actual cable between two named ports returned by pt_devices.

        Use full interface names and an unused switch port per connection. Straight is the
        usual choice for an Ethernet PC, server or routed router port connected to a switch.
        """
        return await invoke(client.connect, a, a_port, b, b_port, cable)

    @mcp.tool(annotations=WRITE)
    async def pt_pc_ip(device: str, address: str, mask: str, gateway: str) -> dict[str, Any]:
        """Set static IPv4 addressing on a PC-PT or Server-PT device."""
        return await invoke(client.pc_ip, device, address, mask, gateway)

    @mcp.tool(annotations=WRITE)
    async def pt_configure_ios(device: str, config: str) -> dict[str, Any]:
        """Submit noninteractive IOS lines. Verify separately; do not batch RSA/password prompts."""
        return await invoke(client.configure_ios, device, config)

    @mcp.tool(annotations=WRITE)
    async def pt_terminal(
        device: str,
        command: str,
        expect_regex: str,
        secret: bool = False,
        timeout: float = 30,
    ) -> dict[str, Any]:
        """Send one real terminal line and wait for fresh output matching the expected tail regex.

        Example expect_regex: R1[>#]\\s*$ or Password:\\s*$. Set secret=true for password input.
        A timeout never retries the command. Inspect the returned output before continuing.
        """
        return await invoke(
            client.terminal, device, command, expect_regex, secret=secret, timeout=timeout
        )

    @mcp.tool(annotations=READ)
    async def pt_read_console(device: str, limit: int = 12000) -> dict[str, Any]:
        """Read real console output with best-effort credential redaction."""
        return await invoke(client.read_console, device, limit)

    @mcp.tool(annotations=WRITE)
    async def pt_export_transcript(device: str, path: str) -> dict[str, Any]:
        """Save actual console output as a redacted UTF-8 .txt file under PT_WORKSPACE."""
        return await invoke(client.export_transcript, device, path)

    @mcp.tool(annotations=WRITE)
    async def pt_move_device(device: str, x: int, y: int) -> dict[str, Any]:
        """Arrange a real device on the live logical canvas."""
        return await invoke(client.move, device, x, y)

    @mcp.tool(annotations=WRITE)
    async def pt_add_note(text: str, x: int, y: int) -> dict[str, Any]:
        """Add a real Packet Tracer canvas note, such as a lab name or addressing label."""
        return await invoke(client.note, text, x, y)

    @mcp.tool(annotations=WRITE)
    async def pt_center_canvas(x: int, y: int) -> dict[str, Any]:
        """Center the live logical workspace. Review the screen before choosing crop coordinates."""
        return await invoke(client.center, x, y)

    @mcp.tool(annotations=WRITE)
    async def pt_save_project(path: str, overwrite: bool = False) -> dict[str, Any]:
        """Ask Packet Tracer to save a real .pkt under PT_WORKSPACE. No file-format synthesis."""
        return await invoke(client.save, path, overwrite=overwrite)

    @mcp.tool(annotations=DESTRUCTIVE)
    async def pt_open_project(path: str, confirm_discard: bool = False) -> dict[str, Any]:
        """Open an existing workspace .pkt and replace the current project."""
        return await invoke(client.open, path, confirm_discard)

    @mcp.tool(annotations=WRITE)
    async def pt_radius_setup(
        server: str,
        client_name: str,
        client_ip: str,
        shared_secret: str,
        username: str,
        password: str,
        auth_port: int = 1645,
    ) -> dict[str, Any]:
        """Add a real Server-PT RADIUS client and user, choose its auth port, and enable AAA.

        Match the router port and shared secret. Credentials are remembered for text redaction.
        """
        return await invoke(
            client.radius_setup,
            server,
            client_name,
            client_ip,
            shared_secret,
            username,
            password,
            auth_port,
        )

    @mcp.tool(annotations=WRITE)
    async def pt_radius_service(server: str, enabled: bool) -> dict[str, Any]:
        """Toggle the actual Server-PT AAA service for a fallback test. Restore it afterward."""
        return await invoke(client.radius_service, server, enabled)

    @mcp.tool(annotations=WRITE, structured_output=False)
    async def pt_capture(
        label: str, crop_box: list[int] | None = None
    ) -> list[TextContent | ImageContent]:
        """Capture the real desktop, retain the original, and return the crop and manifest.

        crop_box is [left, top, right, bottom] in display pixels. Review the live view first.
        No masking, compositing, resizing or generated replacement images are performed.
        """
        record = await invoke(capture, client.workspace, label, crop_box)
        picture = Image(path=str(client.workspace.path(record["crop"]["path"])))
        return [TextContent(type="text", text=json.dumps(record)), picture.to_image_content()]

    @mcp.tool(annotations=READ)
    async def pt_verify_evidence(manifest: str) -> dict[str, Any]:
        """Check SHA-256 and exact crop pixels. This checks integrity, not attestation."""
        return await invoke(verify, client.workspace, manifest)

    @mcp.tool(annotations=WRITE)
    async def pt_fill_report(
        template: str,
        output: str,
        text_values: dict[str, str],
        evidence_values: dict[str, str],
    ) -> dict[str, Any]:
        """Fill {{KEY}} and standalone {{EVIDENCE:key}} placeholders in an existing DOCX copy.

        evidence_values maps keys to verified capture manifests. Styles and tables are kept.
        """
        return await invoke(
            fill_report, client.workspace, template, output, text_values, evidence_values
        )

    if os.getenv("PT_ENABLE_DESKTOP") == "1":

        @mcp.tool(annotations=WRITE)
        async def pt_focus_window(title: str = "Cisco Packet Tracer") -> dict[str, Any]:
            """Linux/X11: focus an existing visible window by title. Requires xdotool."""

            def focus():
                deadline = time.monotonic() + 5
                while True:
                    result = subprocess.run(
                        ["xdotool", "search", "--onlyvisible", "--name", re.escape(title)],
                        capture_output=True,
                        text=True,
                    )
                    if result.returncode == 0:
                        break
                    if time.monotonic() >= deadline:
                        raise RuntimeError(f"Visible window not found: {title}")
                    time.sleep(0.15)
                window = result.stdout.splitlines()[-1]
                subprocess.run(["xdotool", "windowactivate", "--sync", window], check=True)
                time.sleep(0.25)
                return {"window": window}

            return await invoke(focus)

        @mcp.tool(annotations=WRITE)
        async def pt_desktop_action(
            action: Literal["click", "double_click", "key"],
            x: int = 0,
            y: int = 0,
            keys: list[str] | None = None,
        ) -> dict[str, Any]:
            """Operate the actual desktop with a mouse click or key/chord. Optional desktop extra.

            Examples: action=key, keys=[space] for a pager, or keys=[ctrl,c]. Focus PT first.
            """

            def perform():
                import pyautogui

                if action == "key":
                    if not keys or not all(k in pyautogui.KEYBOARD_KEYS for k in keys):
                        raise ValueError("Supply valid PyAutoGUI key names.")
                    pyautogui.hotkey(*keys)
                else:
                    width, height = pyautogui.size()
                    if not 0 <= x < width or not 0 <= y < height:
                        raise ValueError("Mouse coordinates are outside the display.")
                    if action == "click":
                        pyautogui.click(x, y)
                    else:
                        pyautogui.doubleClick(x, y, interval=0.12)
                return {"performed": action}

            return await invoke(perform)

    @mcp.resource("packettracer://workflow")
    def workflow() -> str:
        """The evidence workflow and its verification rules."""
        return WORKFLOW

    @mcp.prompt()
    def record_lab(goal: str) -> str:
        """Start a lab with live verification and genuine screenshots."""
        return f"Complete this authorized Packet Tracer task: {goal}\n\n{WORKFLOW}"

    return mcp
