"""文档对比器测试"""

import pytest
from unittest.mock import AsyncMock


@pytest.fixture
def mock_llm():
    """mock LLM 客户端 — 返回固定摘要"""
    m = AsyncMock()
    m.generate = AsyncMock(return_value="对比摘要：文档v2新增了第3章，修改了金额从500万到650万。")
    return m


class TestComparatorDiff:
    """文本差异检测"""

    def test_identical_texts(self):
        from src.core.comparator import Comparator
        c = Comparator()
        diff = c.compare_texts("你好世界", "你好世界")
        assert diff["identical"] is True
        assert diff["added_lines"] == []
        assert diff["removed_lines"] == []

    def test_added_content(self):
        from src.core.comparator import Comparator
        c = Comparator()
        original = "第一章\n内容A"
        revised = "第一章\n内容A\n第二章\n内容B"
        diff = c.compare_texts(original, revised)
        assert diff["added_lines"] != []
        assert "第二章" in "".join(diff["added_lines"])

    def test_removed_content(self):
        from src.core.comparator import Comparator
        c = Comparator()
        original = "第一章\n内容A\n第二章\n内容B"
        revised = "第一章\n内容A"
        diff = c.compare_texts(original, revised)
        assert diff["removed_lines"] != []
        assert "第二章" in "".join(diff["removed_lines"])

    def test_modified_content(self):
        from src.core.comparator import Comparator
        c = Comparator()
        original = "合同金额：500万元"
        revised = "合同金额：650万元"
        diff = c.compare_texts(original, revised)
        assert diff["line_changes"] > 0
        assert "500万元" in "".join(diff["removed_lines"])
        assert "650万元" in "".join(diff["added_lines"])

    def test_empty_vs_content(self):
        from src.core.comparator import Comparator
        c = Comparator()
        diff = c.compare_texts("", "新内容")
        assert diff["diff_type"] == "新增"
        diff2 = c.compare_texts("旧内容", "")
        assert diff2["diff_type"] == "删除"

    def test_diff_returns_line_details(self):
        from src.core.comparator import Comparator
        c = Comparator()
        diff = c.compare_texts("A\nB\nC", "A\nX\nC")
        assert diff["line_changes"] > 0
        assert "added_lines" in diff
        assert "removed_lines" in diff


class TestComparatorSummary:
    """LLM 摘要生成"""

    def test_summary_includes_input(self, mock_llm):
        import asyncio
        from src.core.comparator import Comparator
        c = Comparator(llm_client=mock_llm)

        original = "合同金额500万"
        revised = "合同金额650万"
        diff = c.compare_texts(original, revised)
        summary = asyncio.run(c.summarize_diff(original, revised, diff))

        assert isinstance(summary, str)
        assert len(summary) > 0
        mock_llm.generate.assert_called_once()
        prompt = mock_llm.generate.call_args.args[0]
        assert "500万" in prompt
        assert "650万" in prompt

    def test_summary_without_llm_returns_structured(self):
        """无 LLM 时返回结构化 diff 数据"""
        from src.core.comparator import Comparator
        c = Comparator()  # 无 llm_client

        diff = c.compare_texts("原版内容", "新版内容")
        assert diff["identical"] is False
        assert "diff_type" in diff
        assert "added_lines" in diff
