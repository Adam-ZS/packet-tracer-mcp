# Headless Linux with Xvfb

Packet Tracer is a graphical simulator. Xvfb gives it a virtual X11 display on
a machine without a monitor. The MCP server uses the local Control Center
mailbox for devices, cables, IOS, IP addressing, pings and `.pkt` saves. Those
operations work with desktop input disabled and without a display environment
in the MCP process.

## Start Packet Tracer

Install Packet Tracer, Xvfb and `xauth`. Use your own account and install the
upstream Control Center module in the Packet Tracer session as described in
the [quick start](../README.md#quick-start). For initial sign-in, module setup
or dialogs, attach to the virtual session with your local X11 viewing tools.
The steps below assume the Packet Tracer launcher is `packettracer`.

```bash
xvfb-run -a -s '-screen 0 1360x768x24 -nolisten tcp' packettracer
```

Leave that session running. Select the Control Center module and click
**Start** in the module dialog if its heartbeat is stale. On installs where
the module is not restored after a restart, add it again in the new session.
Use one Packet Tracer session per mailbox.

## Run the CLI or MCP server without a display

In a second shell, activate the project virtual environment and choose a
workspace. `doctor --live` confirms the mailbox can query Packet Tracer.

```bash
export PT_WORKSPACE="$PWD/workspace"
export PT_ENABLE_DESKTOP=0
env -u DISPLAY -u WAYLAND_DISPLAY -u XAUTHORITY pt-evidence doctor --live
env -u DISPLAY -u WAYLAND_DISPLAY -u XAUTHORITY pt-evidence demo --output practice-lan.pkt
```

The demo uses a blank canvas, configures four devices and checks both pings.
It writes a `.pkt` through Packet Tracer and returns JSON. Use a new output
path for each run. For an MCP client, use `pt-evidence serve` as in the
[client configuration](../README.md#quick-start) with the same workspace.

## Screenshots on the virtual display

For `pt_capture`, start the MCP server with the virtual display's `DISPLAY`
and `XAUTHORITY` so Pillow can capture that session. A virtual X server still
renders the actual Packet Tracer UI. Optional window focus requires an X11
window manager in that session. Credentials and initial setup dialogs are
handled through the normal Packet Tracer interface.
