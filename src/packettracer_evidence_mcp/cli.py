"""Command line entry point. MCP protocol traffic uses stdout only in serve mode."""

from __future__ import annotations

import argparse
import json
import platform
import sys

from . import __version__
from .bridge import FileBridge
from .client import PacketTracer
from .config import Settings, Workspace
from .server import create_server


def main() -> None:
    parser = argparse.ArgumentParser(prog="pt-evidence")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("serve", help="Start the MCP stdio server")
    doctor = commands.add_parser("doctor", help="Check the extension and local configuration")
    doctor.add_argument("--live", action="store_true", help="Also query the live device inventory")
    args = parser.parse_args()
    settings = Settings.from_env()
    client = PacketTracer(FileBridge(settings.bridge_dir), Workspace(settings.workspace))
    if args.command == "serve":
        create_server(client).run(transport="stdio")
        return
    report = client.status()
    report.update(
        {"version": __version__, "platform": platform.system(), "python": platform.python_version()}
    )
    if args.live and report["extension_alive"]:
        try:
            report["devices"] = client.devices()
        except Exception as error:
            report["live_error"] = str(error)
    print(json.dumps(report, indent=2))
    sys.exit(0 if report["extension_alive"] and "live_error" not in report else 1)


if __name__ == "__main__":
    main()
