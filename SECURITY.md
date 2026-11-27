# Security

## Reporting a vulnerability

Use GitHub's **Security → Report a vulnerability** for a private report when
available. Do not publish exploit details, tokens, private captures or student
data in a public issue. If private reporting is unavailable, open an issue
asking for a private contact without including sensitive details.

The project is alpha software. There is no promised response
time or long-term support schedule. Fixes will be documented in the changelog.

## Trust and boundaries

- The server, MCP client, desktop user and separately installed Control Center
  extension are trusted. The mailbox permits code execution inside Packet
  Tracer. Keep it writable only by the intended local user.
- This server exposes stdio, not a network listener. It does not provide an
  arbitrary-JavaScript MCP tool, but device and desktop tools still change a
  live application. Use your MCP client's tool controls.
- Output paths are confined to the configured workspace after symlink
  resolution. This is not an OS sandbox or a defense against a hostile process
  that can change local files or symlinks concurrently.
- Text redaction is best effort. Registered secrets last only for this server
  process. The MCP client's own history may still contain tool arguments.
- Images preserve actual pixels. Full originals can include private content
  outside the crop. Review before sharing; capture fails rather than generating
  a replacement image.
- SHA-256 and crop comparisons check integrity relative to the manifest. They
  do not establish trusted origin, nonrepudiation or cryptographic attestation.
- A bridge timeout can leave an unknown execution outcome. The server never
  automatically repeats a timed-out mutation.

Only one controller should operate a given Packet Tracer session at a time.
The in-process lock cannot coordinate unrelated MCP servers or manual input.
