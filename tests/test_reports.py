from zipfile import ZipFile

import pytest
from docx import Document

from packettracer_evidence_mcp.config import Workspace
from packettracer_evidence_mcp.evidence import capture
from packettracer_evidence_mcp.reports import fill_report, replace_literal


def test_split_run_placeholder_keeps_surrounding_text_and_style():
    doc = Document()
    paragraph = doc.add_paragraph()
    paragraph.add_run("Before {{NA").bold = True
    paragraph.add_run("ME}} after").italic = True
    assert replace_literal(paragraph, "{{NAME}}", "Example User") == 1
    assert paragraph.text == "Before Example User after"
    assert paragraph.runs[0].bold and paragraph.runs[1].italic


def test_report_preserves_styles_headers_tables_and_adds_real_capture(tmp_path, monkeypatch):
    from PIL import Image

    # Explicit fixture for the document plumbing test, not a live capture claim.
    monkeypatch.setattr(
        "packettracer_evidence_mcp.evidence.ImageGrab.grab", lambda: Image.new("RGB", (12, 8))
    )
    workspace = Workspace(tmp_path)
    record = capture(workspace, "TEST FIXTURE")
    doc = Document()
    doc.add_heading("Original template", 0)
    doc.add_paragraph("{{NAME}}")
    doc.add_paragraph("{{EVIDENCE:ping}}")
    doc.add_table(1, 1).cell(0, 0).text = "Keep this table"
    doc.sections[0].header.paragraphs[0].text = "Original header"
    doc.save(tmp_path / "template.docx")
    fill_report(
        workspace,
        "template.docx",
        "filled.docx",
        {"NAME": "Example User"},
        {"ping": record["manifest"]},
    )
    result = Document(tmp_path / "filled.docx")
    assert result.paragraphs[1].text == "Example User"
    assert len(result.inline_shapes) == 1
    assert result.tables[0].cell(0, 0).text == "Keep this table"
    assert result.sections[0].header.paragraphs[0].text == "Original header"
    with ZipFile(tmp_path / "template.docx") as source, ZipFile(tmp_path / "filled.docx") as target:
        assert source.read("word/styles.xml") == target.read("word/styles.xml")
        assert source.read("word/header1.xml") == target.read("word/header1.xml")


def test_missing_placeholder_does_not_write_a_report(tmp_path):
    doc = Document()
    doc.add_paragraph("Original")
    doc.save(tmp_path / "template.docx")
    with pytest.raises(ValueError, match="not found"):
        fill_report(Workspace(tmp_path), "template.docx", "out.docx", {"NAME": "User"}, {})
    assert not (tmp_path / "out.docx").exists()
