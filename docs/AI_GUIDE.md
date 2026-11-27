# AI guide for building a Packet Tracer topology

Use these calls in an MCP client connected to the server. Each JSON example is
the argument object for the named tool. Packet Tracer must be running with
Control Center enabled.

## Choose a workflow

- For a working router, switch, PC and server example, open a blank canvas and
  call `pt_build_practice_lan` with `{"output":"practice-lan.pkt"}`. Check
  `verified`, both `checks` and `saved` in the result.
- For a custom network, follow the sequence below. Start with `pt_status` and
  `pt_devices`. Keep the current project unless the user has authorized a reset.

## Place devices and cable them

Call `pt_add_device` once per device. Canvas coordinates set where each icon
appears. This layout leaves room for labels and links.

| Name | Model | x | y |
| --- | --- | ---: | ---: |
| R1 | `2911` | 280 | 125 |
| SW1 | `2960-24TT` | 560 | 215 |
| PC1 | `PC-PT` | 860 | 145 |
| Server1 | `Server-PT` | 860 | 340 |

`pt_add_device`

```json
{"name":"Server1","model":"Server-PT","x":860,"y":340}
```

Call `pt_devices` again. Use the returned device and full port names in each
`pt_connect` call. A router's model changes its port names. A 2911 commonly
uses `GigabitEthernet0/0`, and an ISR4331 uses `GigabitEthernet0/0/0`.

| Endpoint A | Port A | Endpoint B | Port B | Cable |
| --- | --- | --- | --- | --- |
| R1 | `GigabitEthernet0/0` | SW1 | `FastEthernet0/1` | `straight` |
| PC1 | `FastEthernet0` | SW1 | `FastEthernet0/2` | `straight` |
| Server1 | `FastEthernet0` | SW1 | `FastEthernet0/3` | `straight` |

`pt_connect`

```json
{"a":"Server1","a_port":"FastEthernet0","b":"SW1","b_port":"FastEthernet0/3","cable":"straight"}
```

Each switch port gets one cable. Use `pt_move_device` to reposition an icon
and `pt_add_note` to label links or addresses. Verify the link through
interface status and traffic after the cable request.

## Set addresses and IOS configuration

Use `pt_pc_ip` for both PCs and Server-PT. This example uses a single LAN,
so the 2960 can switch traffic using its default access VLAN.

| Device | Address | Mask | Gateway |
| --- | --- | --- | --- |
| R1 G0/0 | `192.0.2.1` | `255.255.255.0` | |
| PC1 | `192.0.2.2` | `255.255.255.0` | `192.0.2.1` |
| Server1 | `192.0.2.3` | `255.255.255.0` | `192.0.2.1` |

`pt_pc_ip`

```json
{"device":"Server1","address":"192.0.2.3","mask":"255.255.255.0","gateway":"192.0.2.1"}
```

`pt_configure_ios`

```json
{
  "device":"R1",
  "config":"enable\nconfigure terminal\nhostname R1\ninterface g0/0\nip address 192.0.2.1 255.255.255.0\nno shutdown\nend\nwrite memory"
}
```

Inspect `detected_errors`. For a routed topology, add the required routes or
routing protocol. Configure VLAN membership and switch management with IOS
if the task calls for either. For a RADIUS lab, verify addressing first,
then configure Server-PT with `pt_radius_setup` and match the router's
RADIUS settings. See [authentication workflows](WORKFLOWS.md).

## Verify and save

1. On a fresh IOS console, answer `no` if prompted for initial setup and send
   an empty terminal line at `Press RETURN to get started`. Use `enable` when
   privileged EXEC is needed. Check `show ip interface brief` and, when
   appropriate, `show vlan brief` and `show ip route`.
2. From PC1, ping `192.0.2.1` and `192.0.2.3`. Inspect the actual received
   and lost packet counts. Allow time for switching and ARP if the first
   ping loses a packet.

   ```json
   {"device":"PC1","command":"ping 192.0.2.3","expect_regex":"C:\\\\>\\s*$","timeout":20}
   ```

3. Enter interactive answers with individual `pt_terminal` calls. Match the
   current prompt, such as `Password:\s*$` or `R1[>#]\s*$`. Read output before
   continuing after a timeout. Send password inputs with `secret: true`.
4. Save with `pt_save_project` and `{"path":"custom-lan.pkt"}`. If evidence is
   requested, inspect the visible application and capture the relevant pixels
   with `pt_capture`. See the [evidence walkthrough](WORKFLOWS.md).

The same workflow is provided at runtime in the MCP initialization instructions,
the `record_lab` prompt and the `packettracer://workflow` resource.
