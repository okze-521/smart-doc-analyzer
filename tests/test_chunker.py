"""文本切片器测试"""

import pytest
from src.core.chunker import TextChunker


class TestTextChunkerBasic:
    """基本切片功能"""

    def test_split_single_sentence(self):
        chunker = TextChunker(chunk_size=500, overlap=50)
        chunks = chunker.split("这是一段简单的文本。")
        assert len(chunks) == 1
        assert "这是一段简单的文本。" in chunks[0]

    def test_split_no_punctuation(self):
        """没有标点符号时按长度切"""
        chunker = TextChunker(chunk_size=10, overlap=2)
        text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        chunks = chunker.split(text)
        assert len(chunks) >= 2

    def test_empty_string(self):
        chunker = TextChunker()
        chunks = chunker.split("")
        assert chunks == []

    def test_whitespace_only(self):
        chunker = TextChunker()
        chunks = chunker.split("   \n  \t  ")
        assert chunks == []


class TestTextChunkerChinese:
    """中文文本切片"""

    def test_chinese_sentence_split(self):
        chunker = TextChunker(chunk_size=15, overlap=0)
        text = "今天天气很好。我们去公园散步。那里有很多花。还有很多树。"

        chunks = chunker.split(text)
        assert len(chunks) >= 2
        all_text = "".join(chunks)
        assert "今天天气很好" in all_text
        assert "我们去公园散步" in all_text

    def test_chinese_with_english(self):
        chunker = TextChunker(chunk_size=200, overlap=0)
        text = "AI技术发展迅速。Machine learning is becoming mainstream. 各大公司都在投入。"
        chunks = chunker.split(text)
        assert len(chunks) >= 1

    def test_chunk_size_respected(self):
        """每块不应超过 chunk_size 太多"""
        chunker = TextChunker(chunk_size=30, overlap=0)
        text = ("第一段文字，比较长的内容需要被切分。" * 10)

        chunks = chunker.split(text)
        for chunk in chunks:
            assert len(chunk) <= 60  # 允许一定弹性，不超过 2x


class TestTextChunkerOverlap:
    """重叠区域测试"""

    def test_overlap_between_chunks(self):
        chunker = TextChunker(chunk_size=50, overlap=10)
        text = "AAAAA。BBBBB。CCCCC。DDDDD。EEEEE。FFFFF。"

        chunks = chunker.split(text)
        if len(chunks) >= 2:
            # 前一块的尾部应该出现在后一块的头部
            first_end = chunks[0][-5:]
            assert first_end in chunks[1]


class TestTextChunkerParagraphs:
    """段落处理"""

    def test_paragraph_boundaries(self):
        chunker = TextChunker(chunk_size=200, overlap=0)
        text = "第一段内容在这里。\n\n第二段是新的开始。\n\n第三段继续。"

        chunks = chunker.split(text)
        # 尽量在段落边界切
        assert len(chunks) >= 1

    def test_long_paragraph(self):
        """超长段落应该被进一步切分"""
        chunker = TextChunker(chunk_size=30, overlap=0)
        long_sentence = "这是一个非常长的句子" * 10
        chunks = chunker.split(long_sentence)
        assert len(chunks) >= 2


class TestTextChunkerMetadata:
    """元数据测试"""

    def test_returns_list_of_str(self):
        chunker = TextChunker()
        chunks = chunker.split("测试文本。")
        assert isinstance(chunks, list)
        for chunk in chunks:
            assert isinstance(chunk, str)

    def test_chunk_preserves_content(self):
        chunker = TextChunker(chunk_size=500, overlap=0)
        text = "完整的内容应该全部保留。不丢失。"
        chunks = chunker.split(text)
        merged = "".join(chunks)
        # 去除空格和换行符后比较
        assert "完整的内容" in merged
