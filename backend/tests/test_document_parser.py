"""Document parser unit tests.

Verifies:
- Plain text file extraction
- PDF extraction with mock PdfReader
- DOCX extraction with mock Document
- is_readable_file validation
- Corrupt / unsupported file error handling
- clean_extracted_text whitespace and formatting normalization
"""

from unittest.mock import MagicMock, patch
import pytest
from app.utils.document_parser import (
    clean_extracted_text,
    extract_text_from_docx,
    extract_text_from_file,
    extract_text_from_pdf,
    extract_text_from_txt,
    is_readable_file,
)


def test_clean_extracted_text_normalization():
    dirty = "   Hello   World!   \n\n\n\nThis is a   test. \r\n \t  "
    cleaned = clean_extracted_text(dirty)
    assert "Hello World!" in cleaned
    assert "This is a test." in cleaned


def test_clean_extracted_text_empty():
    assert clean_extracted_text("") == ""
    assert clean_extracted_text(None) == ""


def test_extract_txt_file(tmp_path):
    txt_file = tmp_path / "resume.txt"
    txt_file.write_text("Senior Full Stack Engineer\nSkills: Python, TypeScript, React.", encoding="utf-8")
    
    text = extract_text_from_txt(str(txt_file))
    assert "Senior Full Stack Engineer" in text
    assert "TypeScript" in text

    text_via_main = extract_text_from_file(str(txt_file))
    assert "Senior Full Stack Engineer" in text_via_main


def test_extract_pdf_mocked(tmp_path):
    pdf_file = tmp_path / "resume.pdf"
    pdf_file.write_bytes(b"%PDF-1.4 mock content")

    mock_page1 = MagicMock()
    mock_page1.extract_text.return_value = "Page 1: Senior Cloud Architect"
    mock_page2 = MagicMock()
    mock_page2.extract_text.return_value = "Page 2: Kubernetes and Terraform"

    mock_reader = MagicMock()
    mock_reader.pages = [mock_page1, mock_page2]

    with patch("pypdf.PdfReader", return_value=mock_reader):
        text = extract_text_from_pdf(str(pdf_file))
        assert "Senior Cloud Architect" in text
        assert "Kubernetes and Terraform" in text

        # Also via extract_text_from_file
        text_main = extract_text_from_file(str(pdf_file), mime_type="application/pdf")
        assert "Senior Cloud Architect" in text_main


def test_extract_docx_mocked(tmp_path):
    docx_file = tmp_path / "resume.docx"
    docx_file.write_bytes(b"PK mock docx")

    mock_p1 = MagicMock()
    mock_p1.text = "Lead AI Engineer"

    mock_cell1 = MagicMock()
    mock_cell1.text = "Python"
    mock_cell2 = MagicMock()
    mock_cell2.text = "PyTorch"
    mock_row = MagicMock()
    mock_row.cells = [mock_cell1, mock_cell2]
    mock_table = MagicMock()
    mock_table.rows = [mock_row]

    mock_doc = MagicMock()
    mock_doc.paragraphs = [mock_p1]
    mock_doc.tables = [mock_table]

    with patch("docx.Document", return_value=mock_doc):
        text = extract_text_from_docx(str(docx_file))
        assert "Lead AI Engineer" in text
        assert "Python | PyTorch" in text

        text_main = extract_text_from_file(str(docx_file), mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        assert "Lead AI Engineer" in text_main


def test_is_readable_file(tmp_path):
    f = tmp_path / "valid.txt"
    f.write_text("content")
    assert is_readable_file(str(f)) is True

    non_existent = tmp_path / "missing.txt"
    assert is_readable_file(str(non_existent)) is False


def test_unsupported_file_format(tmp_path):
    dummy_file = tmp_path / "resume.xyz"
    dummy_file.write_text("dummy")
    with pytest.raises(ValueError, match="Unsupported file format"):
        extract_text_from_file(str(dummy_file))
