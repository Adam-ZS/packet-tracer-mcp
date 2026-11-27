# Third-party notices

## Packet Tracer Control Center and mailbox protocol

This project requires the separately installed Control Center extension from
[Mats2208/MCP-Packet-Tracer](https://github.com/Mats2208/MCP-Packet-Tracer).
The `req_*.js` / `res_*.txt` mailbox protocol and atomic request publication
pattern in `bridge.py` are adapted from that project's `file_bridge.py`.
Its extension and full MCP server are not bundled or rebranded here.

The upstream license notice is reproduced below.

```text
MIT License

Copyright (c) 2026 Mateo - Packet Tracer MCP Server

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Other dependencies and marks

The official [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
provides the stdio MCP implementation. Pillow provides desktop capture and
lossless cropping. python-docx edits existing Word documents. These libraries
are installed as dependencies and retain their respective licenses.

Cisco and Packet Tracer are marks of Cisco. This independent project is not
affiliated with or endorsed by Cisco and does not distribute Packet Tracer,
Cisco course guides, protected activities or student submissions.

The SVG artwork in `docs/assets/` is original project artwork under this
repository's MIT license. It is a diagram, not screenshot evidence.
