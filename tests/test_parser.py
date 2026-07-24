"""文档解析引擎测试 — PDF / DOCX / XLSX"""

import pytest
from pathlib import Path

from src.core.parser import DocumentParser, ParsedDocument, ParsedSection


class TestDocumentParserPDF:
    """PDF 解析测试"""

    def test_parse_pdf_basic(self, sample_pdf):
        parser = DocumentParser()
        result = parser.parse(sample_pdf)

        assert isinstance(result, ParsedDocument)
        assert result.file_type == "pdf"
        assert result.total_pages >= 1
        assert len(result.full_text) > 0

    def test_parse_pdf_text_content(self, sample_pdf):
        parser = DocumentParser()
        result = parser.parse(sample_pdf)

        assert "Hello PDF World" in result.full_text

    def test_parse_pdf_has_sections(self, sample_pdf):
        parser = DocumentParser()
        result = parser.parse(sample_pdf)

        assert len(result.sections) > 0
        # 所有 section 应该是 ParsedSection 实例
        for section in result.sections:
            assert isinstance(section, ParsedSection)

    def test_parse_pdf_returns_metadata(self, sample_pdf):
        parser = DocumentParser()
        result = parser.parse(sample_pdf)

        assert isinstance(result.metadata, dict)


class TestDocumentParserDOCX:
    """DOCX 解析测试"""

    def test_parse_docx_basic(self, sample_docx):
        parser = DocumentParser()
        result = parser.parse(sample_docx)

        assert isinstance(result, ParsedDocument)
        assert result.file_type == "docx"
        assert len(result.full_text) > 0

    def test_parse_docx_text_content(self, sample_docx):
        parser = DocumentParser()
        result = parser.parse(sample_docx)

        assert "测试文档标题" in result.full_text

    def test_parse_docx_extracts_headings(self, sample_docx):
        parser = DocumentParser()
        result = parser.parse(sample_docx)

        headings = [s for s in result.sections if s.section_type == "heading"]
        assert len(headings) >= 2  # 至少两个标题

    def test_parse_docx_extracts_table(self, sample_docx):
        parser = DocumentParser()
        result = parser.parse(sample_docx)

        tables = [s for s in result.sections if s.section_type == "table"]
        assert len(tables) >= 1
        # 表格应该包含数据
        table = tables[0]
        assert len(table.table_data) >= 1


class TestDocumentParserXLSX:
    """XLSX 解析测试"""

    def test_parse_xlsx_basic(self, sample_xlsx):
        parser = DocumentParser()
        result = parser.parse(sample_xlsx)

        assert isinstance(result, ParsedDocument)
        assert result.file_type == "xlsx"
        assert len(result.full_text) > 0

    def test_parse_xlsx_has_sheet_names(self, sample_xlsx):
        parser = DocumentParser()
        result = parser.parse(sample_xlsx)

        # 工作表名应该出现在元数据中
        assert "Sheet1" in str(result.metadata)

    def test_parse_xlsx_extracts_table_data(self, sample_xlsx):
        parser = DocumentParser()
        result = parser.parse(sample_xlsx)

        tables = [s for s in result.sections if s.section_type == "table"]
        assert len(tables) >= 2  # 两个工作表


class TestDocumentParserErrors:
    """异常处理测试"""

    def test_unsupported_format(self, sample_txt):
        parser = DocumentParser()

        with pytest.raises(ValueError, match="不支持的格式"):
            parser.parse(sample_txt)

    def test_file_not_found(self):
        parser = DocumentParser()

        with pytest.raises(FileNotFoundError):
            parser.parse(Path("/nonexistent/file.pdf"))
