"""Fill explicit placeholders in an existing DOCX without rebuilding its layout."""

from __future__ import annotations

from docx import Document
from docx.shared import Inches
from PIL import Image

from .config import Workspace
from .evidence import verify


def paragraphs(container):
    yield from container.paragraphs
    for table in container.tables:
        seen = set()
        for row in table.rows:
            for cell in row.cells:
                if cell._tc not in seen:
                    seen.add(cell._tc)
                    yield from paragraphs(cell)


def replace_literal(paragraph, token: str, replacement: str) -> int:
    """Replace across runs, retaining surrounding text and the first run's formatting."""
    count = 0
    while token in paragraph.text:
        start = paragraph.text.index(token)
        stop = start + len(token)
        position = 0
        first = True
        for run in paragraph.runs:
            end = position + len(run.text)
            if end > start and position < stop:
                left = max(0, start - position)
                right = min(len(run.text), stop - position)
                run.text = run.text[:left] + (replacement if first else "") + run.text[right:]
                first = False
            position = end
        if first:
            raise ValueError("Placeholder is inside an unsupported Word content control.")
        count += 1
    return count


def fill_report(
    workspace: Workspace,
    template: str,
    output: str,
    text_values: dict[str, str],
    evidence_values: dict[str, str],
) -> dict:
    source = workspace.path(template, suffix=".docx")
    target = workspace.output(output, suffix=".docx")
    doc = Document(source)
    ps = list(paragraphs(doc))
    used = {}
    for key, value in text_values.items():
        token = "{{" + key + "}}"
        if token in value:
            raise ValueError("Replacement text cannot contain its own placeholder.")
        count = sum(replace_literal(p, token, value) for p in ps)
        if not count:
            raise ValueError(f"Text placeholder not found: {token}")
        used[key] = count
    section = doc.sections[0]
    max_width = (section.page_width - section.left_margin - section.right_margin) / 914400
    for key, manifest in evidence_values.items():
        token = "{{EVIDENCE:" + key + "}}"
        matches = [p for p in ps if p.text.strip() == token]
        if not matches:
            raise ValueError(f"Standalone evidence placeholder not found: {token}")
        if not verify(workspace, manifest)["integrity_ok"]:
            raise ValueError(f"Evidence integrity check failed: {key}")
        import json

        record = json.loads(workspace.path(manifest).read_text(encoding="utf-8"))
        image = workspace.path(record["crop"]["path"], suffix=".png")
        for p in matches:
            replace_literal(p, token, "")
            cell_width = getattr(p._parent, "width", None)
            available = min(max_width, cell_width / 914400 - 0.16) if cell_width else max_width
            with Image.open(image) as picture:
                width = min(available, picture.width / 96)
            p.add_run().add_picture(str(image), width=Inches(width))
    doc.save(target)
    return {
        "path": output,
        "text_placeholders": used,
        "evidence_placeholders": list(evidence_values),
    }
