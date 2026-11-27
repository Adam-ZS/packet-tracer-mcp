# Live lab workflows

## A small routed LAN

1. Call `pt_status` and `pt_devices`. Save valuable current work before starting
   another project. New/open operations require `confirm_discard=true`.
2. Add a 2911 router, a 2960 switch and a PC. Inspect the returned ports.
3. Connect router `GigabitEthernet0/0` to switch `FastEthernet0/1`, then PC
   `FastEthernet0` to switch `FastEthernet0/2` with straight-through cables.
4. Configure router `192.0.2.1/24` and PC `192.0.2.2/24`, gateway `192.0.2.1`.
   Use `no shutdown` on the router interface. These are documentation addresses.
5. Wait for switching and ARP to converge. Run `show ip interface brief` and a
   PC ping. Repeat the ping if the initial ARP resolution loses a packet.
6. Read the actual output. Capture the visible successful test and the overall
   topology, with a short descriptive label near each image in the report.
7. Save with `pt_save_project`. Reopen the saved project and check its devices.

The runnable [demo](../examples/build_demo.py) performs the build through an
actual MCP stdio session. It requires an explicit `--discard-current` flag
because it starts a new Packet Tracer project. It never creates screenshot
evidence from text. Open the relevant device window before taking a screenshot.

## Local SSH and AAA

Configure routing before access controls. Keep a working console session open.

Use `pt_terminal` for interactive RSA generation and logins. Enter each answer
only after the expected prompt appears:

```text
crypto key generate rsa  →  How many bits in the modulus [512]:
1024                    →  router configuration prompt
ssh -l operator ...     →  Password:
password input          →  router EXEC prompt
```

The 1024-bit example is for the Packet Tracer teaching exercise, not a general
production recommendation. Follow your device policy on real equipment.

Set `secret=true` for password input. That registers the string for subsequent
text redaction in this server process. It does not remove the password from
MCP client history, the device or a visible screen. Avoid typing credentials
into screenshots. The capture tool never paints over pixels.

`pt_configure_ios` is for noninteractive command blocks. It reports that a
configuration was submitted and explicitly leaves verification to real show
commands and connectivity tests. It does not turn a valid prompt into a claim
that unsupported commands worked.

## RADIUS availability and local fallback

Use `pt_radius_setup` on a Server-PT, matching the router's authentication port
and shared secret. With the legacy host command, inspect the selected image's
default port rather than assuming every platform uses 1812.

Verify these distinct outcomes when testing `group radius local`:

| Server state | Account | Expected observation |
| --- | --- | --- |
| On | Valid RADIUS account | Successful login |
| On | Invalid account | Rejected login |
| On | Local-only account | Rejected when RADIUS rejects it |
| Off/unreachable | Valid local account | Local fallback after server timeout |
| Restored to On | Valid RADIUS account | Successful login again |

An explicit RADIUS rejection does not advance to local fallback. A server
availability failure can. Observe actual results rather than labeling every
failed attempt a server outage. Restore the service and turn off debugging
before saving the final project.

## Screenshot integrity

1. Focus the live window and capture the whole display if the layout is unknown.
2. Choose a crop from that display's dimensions. Include the command and final
   result or prompt, and keep required student identifiers visible in private
   submissions.
3. `pt_capture` saves `original.png`, `crop.png` and `manifest.json` in one
   uniquely named evidence directory. It performs only a rectangular crop.
4. `pt_verify_evidence` checks hashes, dimensions and exact pixel correspondence.
5. Review all visible content before sharing. Hashes do not certify origin.

The SVGs in the README are illustrations. The tests' synthetic pixel fixtures
exercise cropping and tamper detection; they are never labeled as live lab
evidence.

## Preserve a Word template

Copy your template into `PT_WORKSPACE`. Put `{{NAME}}`, `{{STUDENT_ID}}` or
`{{ANSWER_1}}` where text belongs. Put `{{EVIDENCE:ping}}` alone in the
paragraph where the verified image belongs. A separate caption paragraph can
contain `{{CAPTION_PING}}`.

Call `pt_fill_report` with:

```json
{
  "template": "templates/lab.docx",
  "output": "reports/completed.docx",
  "text_values": {"NAME": "Example User", "CAPTION_PING": "PC reaches the router"},
  "evidence_values": {"ping": "evidence/<capture-id>/manifest.json"}
}
```

Only explicit body/table placeholders are filled. Headers, footers, styles,
question order and existing tables stay in the template. Placeholders in Word
content controls are not supported. Render and inspect the resulting report;
adding content naturally changes pagination. In table cells or multi-section
layouts, review image width and fit before submission.
