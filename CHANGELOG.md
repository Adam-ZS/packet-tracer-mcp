# Changelog

## 0.2.0

- Add `pt_build_practice_lan` for a cabled router, switch, PC and server. It tests
  the PC's reachability to the router and server before saving.
- Give MCP clients concrete runtime instructions for placing devices, choosing
  exact ports, connecting cables, configuring IP and verifying a custom lab.
- Add a lightweight `pt-evidence demo` CLI and a tested Xvfb setup for
  running the simulator on Linux without a physical display.
- Rename the GitHub repository to `packet-tracer-mcp`. The Python package and
  `pt-evidence` command retain their existing names.

## 0.1.0

- Typed live Packet Tracer controls for a focused set of routers, switches,
  PCs and servers through the upstream Control Center mailbox.
- Interactive terminal input waits for fresh output and an expected final
  prompt, with explicit timeout results and best-effort text redaction.
- Genuine desktop capture retains original pixels, lossless crops and SHA-256
  manifests. Verification compares exact crop pixels as well as hashes.
- Server-PT RADIUS configuration and service toggling for fallback tests.
- Existing DOCX templates can be filled through explicit text and evidence
  placeholders while retaining their structure.
- Stdio integration tests, offline regression tests, CI, setup documentation,
  original SVG diagrams and community contribution files.

Live operation has been checked on Linux/X11. Other desktops remain unverified.
