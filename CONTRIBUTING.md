# Contributing

Small, reproducible changes are welcome. Useful areas include model-specific
behavior, prompt timing, capture support on additional desktops, report layout
and clear setup documentation.

## Set up

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
ruff check .
ruff format --check .
python -m build
```

Offline tests must pass without Packet Tracer, a Cisco login or a display.
Tests may use explicitly labeled synthetic fixtures. Never present those
fixtures as screenshots of a running application.

## Live checks

Live checks are manual and opt-in because they change an open application.
Save your work first, install the upstream extension, run `doctor --live`,
then use the neutral documentation-address demo. Verify actual command
output, screenshot crops and saved-file reopening. State which OS, image and
extension you tested. Do not infer cross-platform support from unit tests.

## Pull requests

Describe the concrete problem, resulting behavior and checks performed.
Keep changes focused. Add a regression test when it checks a meaningful
failure mode. Document unsupported commands and uncertain results honestly.
Preserve attribution when adapting upstream code.

Do not commit private `.pkt`/`.pka` projects, student reports, Cisco guides,
account details, tokens or full desktop captures containing personal data.
The `.gitignore` excludes common output files; review the staged diff too.

By contributing, you agree that your contribution can be distributed under
this project's MIT license. Follow the [code of conduct](CODE_OF_CONDUCT.md).
