"""文本切片器 — 语义边界切分，支持中英文"""

import re


class TextChunker:
    """按语义边界将长文本切分为 RAG 友好的块"""

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = min(overlap, chunk_size // 2)  # 重叠不超过 chunk 一半

    # ----------------------------------------------------------------
    #  入口
    # ----------------------------------------------------------------

    def split(self, text: str) -> list[str]:
        """切分文本，返回 chunk 列表"""
        if not text or not text.strip():
            return []

        # 1. 按段落初步分割
        paragraphs = self._split_paragraphs(text)

        # 2. 每个段落内部按句子边界切
        chunks: list[str] = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            if len(para) <= self.chunk_size:
                chunks.append(para)
            else:
                # 长段落 -> 按句子进一步切
                sentences = self._split_sentences(para)
                chunks.extend(self._merge_sentences(sentences))

        # 3. 添加重叠
        return self._add_overlap(chunks)

    # ----------------------------------------------------------------
    #  子步骤
    # ----------------------------------------------------------------

    def _split_paragraphs(self, text: str) -> list[str]:
        """按双换行 / 连续空行切段落"""
        return re.split(r"\n\s*\n", text)

    def _split_sentences(self, text: str) -> list[str]:
        """
        按中英文标点切句。
        中文: 。！？…
        英文: . ! ? 后跟空格/大写/结尾
        """
        # 正则：在中英文句末标点后切分，保留标点在前一句
        pattern = r"(?<=[。！？…\.\!\?])(?=\s|$|[A-Z\u4e00-\u9fff])"
        parts = re.split(pattern, text)

        # 合并过短的片段
        sentences: list[str] = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if sentences and len(sentences[-1]) < 20:
                # 过短的前一句并到当前句
                sentences[-1] = sentences[-1] + part
            else:
                sentences.append(part)

        return sentences

    def _merge_sentences(self, sentences: list[str]) -> list[str]:
        """将短句子合并成不超过 chunk_size 的块"""
        chunks: list[str] = []
        current = ""

        for sentence in sentences:
            if not sentence.strip():
                continue

            # 如果当前块 + 新句子超限，保存当前块并开始新块
            if current and len(current) + len(sentence) > self.chunk_size:
                chunks.append(current)
                current = sentence
            elif current:
                current += sentence
            else:
                # 第一句可能本身就超长（比如长串英文无标点）
                if len(sentence) > self.chunk_size * 2:
                    # 强制按固定长度切
                    chunks.extend(self._force_split(sentence))
                else:
                    current = sentence

        if current:
            chunks.append(current)

        return chunks

    def _force_split(self, text: str) -> list[str]:
        """超长无标点文本强制按 chunk_size 切"""
        chunks = []
        for i in range(0, len(text), self.chunk_size):
            chunks.append(text[i:i + self.chunk_size])
        return chunks

    def _add_overlap(self, chunks: list[str]) -> list[str]:
        """在相邻块之间添加重叠区域"""
        if self.overlap <= 0 or len(chunks) <= 1:
            return chunks

        result = [chunks[0]]
        for i in range(1, len(chunks)):
            prev = chunks[i - 1]
            curr = chunks[i]

            # 取前一块尾部的 overlap 字符加到当前块头部
            overlap_text = prev[-self.overlap:]
            result.append(overlap_text + curr)

        return result
