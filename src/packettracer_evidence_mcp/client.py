"""Small typed operations over Packet Tracer's live Extensions API."""

from __future__ import annotations

import ipaddress
import json
import re
import time

from .bridge import FileBridge
from .config import Workspace
from .redaction import Redactor

MODELS = {"2911": 0, "ISR4331": 0, "2960-24TT": 1, "PC-PT": 8, "Server-PT": 9}
CABLES = {"straight": 8100, "crossover": 8101, "serial": 8106}


def js(value: object) -> str:
    return json.dumps(value, ensure_ascii=True)


def device_placement(name: str, model: str, x: int, y: int) -> str:
    return f"lwAddDevice({js(name)},{MODELS[model]},{js(model)},{int(x)},{int(y)});"


def cable_placement(a: str, a_port: str, b: str, b_port: str, cable: str) -> str:
    return (
        f"var a=ipc.network().getDevice({js(a)}),b=ipc.network().getDevice({js(b)});"
        "if(!a||!b)throw new Error('Device not found');"
        f"if(!a.getPort({js(a_port)})||!b.getPort({js(b_port)}))"
        "throw new Error('Port not found; inspect the actual model ports first');"
        f"lwAddLink({js(a)},{js(a_port)},{js(b)},{js(b_port)},{CABLES[cable]});"
    )


class PacketTracer:
    def __init__(self, bridge: FileBridge, workspace: Workspace):
        self.bridge = bridge
        self.workspace = workspace
        self.redactor = Redactor()

    def _execute(self, body: str) -> object:
        source = (
            "try{var value=(function(){" + body + "})();"
            "reportResult(JSON.stringify({ok:true,value:value}));}catch(e){"
            "reportResult(JSON.stringify({ok:false,error:String(e)}));}"
        )
        raw = self.bridge.request(source)
        try:
            result = json.loads(raw)
        except (ValueError, TypeError) as error:
            raise RuntimeError(
                "Unexpected extension response. Check Control Center compatibility."
            ) from error
        if not result.get("ok"):
            raise RuntimeError(
                self.redactor.filter(str(result.get("error", "Packet Tracer error")))
            )
        return result.get("value")

    def status(self) -> dict:
        return {
            "bridge_directory": str(self.bridge.directory),
            "heartbeat_age_seconds": self.bridge.heartbeat_age(),
            "extension_alive": self.bridge.alive(),
            "workspace": str(self.workspace.root),
        }

    def devices(self) -> list[dict]:
        return self._execute(
            "var n=ipc.network(),out=[];for(var i=0;i<n.getDeviceCount();i++){"
            "var d=n.getDeviceAt(i),ports=[];for(var p=0;p<d.getPortCount();p++)"
            "ports.push(d.getPortAt(p).getName());"
            "out.push({name:d.getName(),model:d.getModel(),ports:ports,"
            "x:d.getCenterXCoordinate(),y:d.getCenterYCoordinate()});}return out;"
        )

    def new(self, confirm_discard: bool) -> dict:
        if not confirm_discard:
            raise ValueError("Starting a new project requires confirm_discard=true.")
        return {"result": self._execute("ipc.appWindow().fileNew(false);return 'new project';")}

    def project_info(self, name: str, description: str, additional_info: str = "") -> dict:
        self._execute(
            "var f=ipc.appWindow().getActiveFile(),u=f.getUserProfile();"
            f"f.setNetworkDescription({js(description)});u.setName({js(name)});"
            f"u.setEmail('');u.setAddInfo({js(additional_info)});return true;"
        )
        return {"name": name, "description": description, "additional_info": additional_info}

    def add_device(self, name: str, model: str, x: int, y: int) -> dict:
        if not name.strip() or len(name) > 100:
            raise ValueError("Use a device name between 1 and 100 characters.")
        if model not in MODELS:
            raise ValueError(f"Supported model choices: {', '.join(MODELS)}")
        return self._execute(
            f"if(ipc.network().getDevice({js(name)}))throw new Error('Device already exists');"
            + device_placement(name, model, x, y)
            + f"var d=ipc.network().getDevice({js(name)});"
            "if(!d)throw new Error('Device was not created');"
            "return {name:d.getName(),model:d.getModel()};"
        )

    def connect(self, a: str, a_port: str, b: str, b_port: str, cable: str) -> dict:
        if cable not in CABLES:
            raise ValueError("Cable must be straight, crossover or serial.")
        return self._execute(
            cable_placement(a, a_port, b, b_port, cable)
            + "return {requested:true,verified:false,note:'Check port status and connectivity.'};"
        )

    def pc_ip(self, name: str, address: str, mask: str, gateway: str) -> dict:
        interface = ipaddress.IPv4Interface(f"{address}/{mask}")
        gateway_ip = ipaddress.IPv4Address(gateway)
        if gateway_ip not in interface.network:
            raise ValueError("The default gateway must be in the PC subnet.")
        self._execute(
            f"configurePcIp({js(name)},false,{js(str(interface.ip))},"
            f"{js(str(interface.netmask))},{js(str(gateway_ip))});return true;"
        )
        return {"device": name, "address": address, "mask": mask, "gateway": gateway}

    def build_practice_lan(self, output: str) -> dict:
        """Build and verify a fixed starter network on a blank logical canvas."""
        with self.bridge.lock:
            if self.workspace.path(output, suffix=".pkt").exists():
                raise FileExistsError(f"Output already exists: {output}")
            if any(device["model"] != "Power Distribution Device" for device in self.devices()):
                raise ValueError(
                    "Open a blank Packet Tracer project before building the practice LAN."
                )

            devices = [
                ("R-DEMO", "2911", 280, 125),
                ("SW-DEMO", "2960-24TT", 560, 215),
                ("PC-DEMO", "PC-PT", 860, 145),
                ("SERVER-DEMO", "Server-PT", 860, 340),
            ]
            links = [
                ("R-DEMO", "GigabitEthernet0/0", "FastEthernet0/1"),
                ("PC-DEMO", "FastEthernet0", "FastEthernet0/2"),
                ("SERVER-DEMO", "FastEthernet0", "FastEthernet0/3"),
            ]
            # One mailbox round trip for the fixed topology. Ping checks validate the links later.
            self._execute(
                "".join(device_placement(*spec) for spec in devices)
                + "".join(
                    cable_placement(device, port, "SW-DEMO", switch_port, "straight")
                    for device, port, switch_port in links
                )
                + "return true;"
            )

            for device, address in [("PC-DEMO", "192.0.2.2"), ("SERVER-DEMO", "192.0.2.3")]:
                self.pc_ip(device, address, "255.255.255.0", "192.0.2.1")

            router_config = "\n".join(
                [
                    "enable",
                    "configure terminal",
                    "hostname R-DEMO",
                    "interface g0/0",
                    "ip address 192.0.2.1 255.255.255.0",
                    "no shutdown",
                    "end",
                    "write memory",
                ]
            )
            result = self.configure_ios("R-DEMO", router_config)
            if result["detected_errors"]:
                raise RuntimeError(f"Router reported errors: {result['detected_errors']}")

            # These three ports terminate at a routed interface or a host.
            # PortFast avoids waiting for the initial STP timer on this fixed layout.
            switch_config = "\n".join(
                [
                    "enable",
                    "configure terminal",
                    "hostname SW-DEMO",
                    "interface range f0/1 - 3",
                    "switchport mode access",
                    "spanning-tree portfast",
                    "end",
                    "write memory",
                ]
            )
            result = self.configure_ios("SW-DEMO", switch_config)
            if result["detected_errors"]:
                raise RuntimeError(f"Switch reported errors: {result['detected_errors']}")

            notes = [
                (420, 35, "Practice LAN | 192.0.2.0/24"),
                (190, 170, "R-DEMO G0/0\n192.0.2.1/24"),
                (470, 255, "SW-DEMO\nF0/1 router | F0/2 PC | F0/3 server"),
                (900, 140, "PC-DEMO\n192.0.2.2/24"),
                (900, 325, "SERVER-DEMO\n192.0.2.3/24"),
            ]
            self._execute(
                "var w=ipc.appWindow().getActiveWorkspace().getLogicalWorkspace();"
                + "".join(
                    f"w.addNote({x},{y},w.getIncNoteZOrder(),{js(label)});" for x, y, label in notes
                )
                + "w.centerOn(570,220);return true;"
            )

            checks = []
            for destination in ["192.0.2.1", "192.0.2.3"]:
                for attempt in range(1, 6):
                    ping = self.terminal("PC-DEMO", f"ping {destination}", r"C:\\>\s*$", timeout=12)
                    # Parse completed ping statistics rather than accepting a prompt alone.
                    passed = ping["matched"] and bool(
                        re.search(r"Lost\s*=\s*0\s*\(0% loss\)", ping["new_output"])
                    )
                    if passed or ping["timed_out"]:
                        break
                    if attempt < 5:
                        time.sleep(2)
                checks.append(
                    {
                        "source": "PC-DEMO",
                        "destination": destination,
                        "passed": passed,
                        "attempts": attempt,
                        "output": ping["new_output"],
                    }
                )
                if not passed:
                    return {
                        "verified": False,
                        "saved": False,
                        "checks": checks,
                        "next_step": "Inspect the live LAN and the returned ping output.",
                    }
            return {"verified": True, "checks": checks, **self.save(output)}

    def snapshot(self, name: str) -> dict:
        return self._execute(
            f"var d=ipc.network().getDevice({js(name)});"
            "if(!d)throw new Error('Device not found');var c=d.getCommandLine();"
            "return {prompt:String(c.getPrompt()),output:String(c.getOutput())};"
        )

    def read_console(self, name: str, limit: int = 12000) -> dict:
        if not 100 <= limit <= 100000:
            raise ValueError("Output limit must be between 100 and 100000 characters.")
        result = self.snapshot(name)
        result["output"] = self.redactor.filter(result["output"][-limit:])
        return result

    def terminal(
        self,
        name: str,
        command: str,
        expect_regex: str,
        *,
        secret: bool = False,
        timeout: float = 30,
    ) -> dict:
        if "\n" in command or "\r" in command:
            raise ValueError(
                "Send one line at a time. Use pt_configure_ios for noninteractive config."
            )
        if not 1 <= timeout <= 90 or len(expect_regex) > 300:
            raise ValueError(
                "Timeout must be 1..90 seconds and the expected regex at most 300 chars."
            )
        expected = re.compile(expect_regex)
        with self.bridge.lock:
            before = self.snapshot(name)["output"]
            if secret:
                self.redactor.remember(command)
            self._execute(
                f"ipc.network().getDevice({js(name)}).getCommandLine().enterCommand({js(command)});"
                "return true;"
            )
            deadline = time.monotonic() + timeout
            matched = False
            actual = self.snapshot(name)
            while True:
                changed = actual["output"] != before
                # Matching only the terminal tail avoids accepting a historical prompt.
                tail = "\n".join(actual["output"].rstrip().splitlines()[-4:])
                matches = list(expected.finditer(tail))
                match = matches[-1] if matches else None
                matched = changed and match is not None and match.end() == len(tail)
                if matched or time.monotonic() >= deadline:
                    break
                time.sleep(0.15)
                actual = self.snapshot(name)
            delta = (
                actual["output"][len(before) :]
                if actual["output"].startswith(before)
                else actual["output"]
            )
            return {
                "matched": matched,
                "timed_out": not matched,
                "prompt": actual["prompt"],
                "new_output": self.redactor.filter(delta[-12000:]),
                "output_tail": self.redactor.filter(actual["output"][-12000:]),
                "note": "A matching prompt does not prove success. Inspect the actual output.",
            }

    def configure_ios(self, name: str, config: str) -> dict:
        if not config.strip() or len(config) > 30000:
            raise ValueError("Configuration must contain 1..30000 characters.")
        with self.bridge.lock:
            before = self.snapshot(name)["output"]
            self._execute(f"configureIosDevice({js(name)},{js(config)});return true;")
            actual = self.snapshot(name)["output"]
            delta = actual[len(before) :] if actual.startswith(before) else actual
            errors = re.findall(
                r"% (?:Invalid input[^\n]*|Incomplete command[^\n]*|Ambiguous command[^\n]*)", delta
            )
            return {
                "submitted": True,
                "verified": False,
                "detected_errors": errors,
                "output": self.redactor.filter(delta[-12000:]),
                "next_step": "Verify using live show commands and connectivity tests.",
            }

    def move(self, name: str, x: int, y: int) -> dict:
        self._execute(
            f"ipc.network().getDevice({js(name)}).moveToLocationCentered({int(x)},{int(y)});"
            "return true;"
        )
        return {"device": name, "x": x, "y": y}

    def note(self, text: str, x: int, y: int) -> dict:
        value = self._execute(
            "var w=ipc.appWindow().getActiveWorkspace().getLogicalWorkspace();"
            f"return String(w.addNote({int(x)},{int(y)},w.getIncNoteZOrder(),{js(text)}));"
        )
        return {"note_id": value}

    def center(self, x: int, y: int) -> dict:
        self._execute(
            "ipc.appWindow().getActiveWorkspace().getLogicalWorkspace()."
            f"centerOn({int(x)},{int(y)});return true;"
        )
        return {"x": x, "y": y}

    def save(self, relative: str, *, overwrite: bool = False) -> dict:
        target = self.workspace.output(relative, suffix=".pkt", overwrite=overwrite)
        previous_mtime = target.stat().st_mtime_ns if target.exists() else None
        require_update = False
        if previous_mtime is not None:
            current = self._execute(
                "return String(ipc.appWindow().getActiveFile().getSavedFilename());"
            )
            if str(target) == current:
                # Save As on an existing path opens a modal overwrite dialog and stalls the bridge.
                result = self._execute("return ipc.appWindow().fileSave();")
            else:
                filename = self._execute(
                    f"ipc.appWindow().fileSaveAsNoPrompt({js(str(target))},false);"
                    "return String(ipc.appWindow().getActiveFile().getSavedFilename());"
                )
                result = filename == str(target)
                require_update = True
        else:
            result = self._execute(f"return ipc.appWindow().fileSaveAs({js(str(target))});")
        if result is not True:
            raise RuntimeError(f"Packet Tracer did not confirm saving: {result}")
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            updated = target.is_file() and target.stat().st_mtime_ns != previous_mtime
            if target.is_file() and target.stat().st_size > 0 and (updated or not require_update):
                return {"saved": True, "path": relative, "bytes": target.stat().st_size}
            time.sleep(0.15)
        raise RuntimeError("Packet Tracer accepted the save, but no nonempty file was observed.")

    def open(self, relative: str, confirm_discard: bool) -> dict:
        if not confirm_discard:
            raise ValueError(
                "Opening a file requires confirm_discard=true for the current project."
            )
        target = self.workspace.path(relative, suffix=".pkt")
        if not target.is_file():
            raise FileNotFoundError(relative)
        result = self._execute(f"return ipc.appWindow().fileOpen({js(str(target))});")
        # AppWindow::fileOpen returns 0 on success, unlike fileSaveAs's bool.
        return {"opened": result == 0 and result is not False, "result": result, "path": relative}

    def radius_setup(
        self,
        server: str,
        client_name: str,
        client_ip: str,
        shared_secret: str,
        username: str,
        password: str,
        auth_port: int = 1645,
    ) -> dict:
        ipaddress.IPv4Address(client_ip)
        if not 1 <= auth_port <= 65535:
            raise ValueError("Invalid RADIUS port.")
        self.redactor.remember(shared_secret)
        self.redactor.remember(password)
        return self._execute(
            f"var s=ipc.network().getDevice({js(server)}),a=s.getProcess('AcsServer');"
            f"var c=a.addToClientMap({js(client_ip)},1,{js(client_name)},{js(shared_secret)});"
            f"var u=a.addToUserMap({js(username)},'Lab account',{js(password)});"
            f"s.getProcess('RadiusServer').setPort({auth_port});a.enableACSServerService(true);"
            "return {client_added:c,user_added:u,enabled:a.isEnabled(),"
            "auth_port:s.getProcess('RadiusServer').getPort()};"
        )

    def radius_service(self, server: str, enabled: bool) -> dict:
        return self._execute(
            f"var a=ipc.network().getDevice({js(server)}).getProcess('AcsServer');"
            f"a.enableACSServerService({js(enabled)});return {{enabled:a.isEnabled()}};"
        )

    def export_transcript(self, name: str, relative: str) -> dict:
        target = self.workspace.output(relative, suffix=".txt")
        text = self.redactor.filter(self.snapshot(name)["output"])
        target.write_text(text, encoding="utf-8")
        return {"path": str(target.relative_to(self.workspace.root)), "redaction": "best effort"}
