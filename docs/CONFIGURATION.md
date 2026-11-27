# Configuration

The MCP server and Packet Tracer must run as the same desktop user on the same
machine. Install the Control Center extension separately from the
[upstream releases](https://github.com/Mats2208/MCP-Packet-Tracer/releases).
Enable it in Packet Tracer's scripting module settings.

| Variable | Default | Meaning |
| --- | --- | --- |
| `PT_WORKSPACE` | `./workspace` relative to the server's working directory | Root for all captures, transcripts, templates and saved projects |
| `PT_BRIDGE_DIR` | Discover an existing mailbox | Explicit Control Center directory containing `alive.txt` |
| `PT_ENABLE_DESKTOP` | Off | Set to `1` to expose mouse/key and window-focus tools |
| `DISPLAY` | Inherited from desktop session | X11 display used by screenshot and optional input tools |

Paths in MCP calls are relative to `PT_WORKSPACE`. Absolute paths, traversal
and symlinks that resolve outside it are rejected. Copy a report template into
the workspace before editing it. Existing output files are protected; the
project-save tool has an explicit `overwrite` option.

Discovery checks the user's state directory, `AppData/Local`, and the legacy
`.packet-tracer-mcp` location. On Windows it also checks `LOCALAPPDATA`.
If several heartbeat files exist, it chooses the most recently updated one.
`PT_BRIDGE_DIR` always overrides discovery. The transport never creates a
missing external mailbox or installs an extension silently.

## Linux/X11 desktop tools

```bash
python -m pip install -e '.[desktop]'
# Install xdotool with your distribution's package manager if it is absent.
export PT_ENABLE_DESKTOP=1
pt-evidence doctor --live
```

In your MCP client's environment add `"PT_ENABLE_DESKTOP": "1"`. These two
optional tools act on your actual desktop. Focus Packet Tracer first and
review the screen after layout changes. Coordinates are display pixels,
not Packet Tracer's logical canvas coordinates.

`pt_focus_window` requires `xdotool`. Mouse and key input requires PyAutoGUI.
The main capture path uses Pillow's `ImageGrab`, not PyAutoGUI screenshots.
There is no invented or rendered-image fallback when capture fails.

Wayland capture and focus behavior is not verified. Use an X11 session for
the tested workflow. Windows and macOS transport path handling is included,
but end-to-end operation on those systems has not been verified.

## SDK compatibility

This release uses the official [MCP Python SDK v1 API](https://github.com/modelcontextprotocol/python-sdk/tree/v1.x),
with `mcp>=1.30,<2`. The upper bound is intentional: a future major SDK version
can change server APIs. MCP clients only need standard stdio tool support;
they do not need the Python SDK installed in their own environment.
