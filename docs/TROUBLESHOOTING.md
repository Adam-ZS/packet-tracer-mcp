# Troubleshooting

| Symptom | Check |
| --- | --- |
| `extension_alive` is false | Packet Tracer is open, the upstream Control Center extension is enabled, and `PT_BRIDGE_DIR` points to its current mailbox |
| Heartbeat exists but remains stale | Restart or re-enable the scripting module; a blocked application dialog can prevent its timer from running |
| `lwAddDevice` or `configureIosDevice` is missing | Install the compatible upstream Control Center extension, not an unrelated scripting module |
| Router model fails | Use `ISR4331` rather than `4331`; use `pt_devices` to check what actually exists |
| Interface command is rejected | Inspect model ports: 2911 uses G0/0, while ISR4331 uses G0/0/0 |
| Terminal wait times out | Read the output before sending anything else; check for setup, password, RSA-size or `--More--` prompts |
| A command times out at the bridge | Its outcome may be unknown. Inspect live state before retrying any mutation |
| First ping loses a packet | Wait for links/STP/ARP and repeat; capture the actual successful result |
| Local fallback is rejected with RADIUS On | A RADIUS rejection ends that attempt. Disable the test service to test availability fallback, then restore it |
| Screenshot fails | Confirm a supported logged-in desktop; the verified workflow uses Linux/X11 |
| Screenshot shows another window | Focus PT, close overlays, inspect the display, then capture again |
| Last terminal lines are missing from a crop | Recheck display/window geometry and include the final prompt; do not assume every device dialog has the same size |
| Output path is rejected | Use a path relative to `PT_WORKSPACE`; copy outside templates into the workspace first |
| Evidence verification fails | Check the original, crop and manifest belong together and have not been edited |
| Template placeholder is not found | Use exact `{{KEY}}` text, or a standalone `{{EVIDENCE:key}}` paragraph; Word content controls are unsupported |

Use `pt-evidence doctor --live` for an initial diagnosis. Its JSON can include
device names and local paths, so review it before posting an issue. Supply
the OS, Packet Tracer version, extension version, steps and redacted error.
Do not attach course submissions, IDs, real passwords or protected activities.
