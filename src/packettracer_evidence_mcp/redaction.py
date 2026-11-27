"""Best-effort transcript filtering. Screenshot pixels are never redacted."""

from __future__ import annotations

import re


class Redactor:
    def __init__(self) -> None:
        self._secrets: set[str] = set()

    def remember(self, value: str) -> None:
        if value:
            self._secrets.add(value)

    def filter(self, text: str) -> str:
        for secret in sorted(self._secrets, key=len, reverse=True):
            text = text.replace(secret, "[REDACTED]")
        # IOS credential lines, including encrypted forms, and legacy RADIUS keys.
        text = re.sub(
            r"(?im)^(.*?\b(?:secret|password|radius-server key)\s+).+$",
            r"\1[REDACTED]",
            text,
        )
        return text
