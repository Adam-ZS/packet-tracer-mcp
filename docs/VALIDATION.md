# Validation record

## Four-device demo and headless Linux

Version 0.2.0 was tested on Cisco Packet Tracer 9.0.1 with Control Center
0.5.2 running on Xvfb. The MCP test client and server ran without `DISPLAY`,
`WAYLAND_DISPLAY` or `XAUTHORITY`. The tool created four devices and three
cables, configured the router and switch IOS and both host addresses, and
received four replies with zero loss from both the router and the server.
Packet Tracer saved the `.pkt` and reopened it with all four devices.
The tool call took about 12 seconds after MCP startup. The separate terminal
demo took about 13 seconds. Timing varies with the workstation and session.

The current README PNGs are crops of the actual virtual display. Both crop
manifests passed hash and pixel verification before the crops were copied
into the repository.

## Offline checks

The regression suite covers:

- Atomic UTF-8 mailbox publication, unique request IDs across instances,
  heartbeat failure, timeout cleanup and absence of automatic retries.
- Workspace traversal, absolute paths, symlink escape and overwrite handling.
- Exact crop pixels and hashes, altered pixels with a recomputed hash,
  invalid coordinates, unavailable capture and malicious manifest paths.
- Historical console prompts, fresh output matching and credential filtering.
- Split-run Word placeholders, template styles/headers/tables and missing
  placeholders.
- Native save rejection and the existing-file overwrite modal regression.
- An actual MCP stdio handshake, tool schemas, resource/prompt discovery and
  error recovery while the Packet Tracer bridge is offline.

Synthetic pixel and console fixtures are explicitly labeled in the test
source. They test software behavior and are not presented as live evidence.

## Live checks

Environment: Linux/X11, Python 3.14.7, MCP Python SDK 1.30.0, Pillow 12.3.0,
and the installed upstream Control Center file mailbox.

Through a real MCP stdio client session:

1. Inspected device model and actual port names.
2. Started a new neutral project and cleared personal profile fields.
3. Created a 2911 router, 2960 switch and PC-PT, connected their real ports,
   configured `192.0.2.0/24`, and added canvas notes.
4. Read the router console and verified `show ip interface brief` on the
   2911 image reporting IOS 15.1(4)M5. The connected port was up/up.
5. Ran actual PC-to-router pings with four replies and zero packet loss.
6. Captured the live topology and terminal with `pt_capture`. Verified hashes
   and exact crop pixels. Checked that the PNG returned over MCP had the same
   SHA-256 hash as the saved crop.
7. Filled a separate neutral DOCX template using those real capture manifests.
8. Saved a real `.pkt`, saved changes again without an overwrite modal,
   reopened it, and checked the expected devices.

Originals, manifests, transcripts and demo projects remain in the local
workspace. Run the example to create your own artifacts.

## Limits

This does not establish full IOS feature support, broad device coverage,
Windows/macOS live compatibility or Wayland capture support. Screenshot
integrity is not trusted origin attestation. A successful prompt match alone
does not establish that a command was accepted. RADIUS port, source address
and fallback behavior must be checked on the selected image and topology.
