"""文档对比引擎 — difflib + LLM 摘要"""

import difflib
from typing import Any


class Comparator:
    """两个文档的文本级差异检测 + LLM 智能摘要"""

    def __init__(self, llm_client: Any = None):
        self.llm = llm_client

    # ── 文本对比 ────────────────────────────────

    def compare_texts(self, original: str, revised: str) -> dict:
        """对比两段文本，返回结构化差异"""
        if not original and not revised:
            return self._no_diff()

        if not original:
            return self._all_added(revised)

        if not revised:
            return self._all_removed(original)

        # 逐行差异（difflib unified diff）
        original_lines = original.splitlines(keepends=True)
        revised_lines = revised.splitlines(keepends=True)

        differ = difflib.unified_diff(
            original_lines, revised_lines,
            fromfile="original", tofile="revised",
        )

        added_lines: list[str] = []
        removed_lines: list[str] = []
        changed_count = 0

        for line in differ:
            if line.startswith("---") or line.startswith("+++"):
                continue
            if line.startswith("@@"):
                continue
            if line.startswith("+"):
                added_lines.append(line[1:].rstrip("\n"))
                changed_count += 1
            elif line.startswith("-"):
                removed_lines.append(line[1:].rstrip("\n"))
                changed_count += 1

        if changed_count == 0:
            return self._no_diff()

        # 判断差异类型
        diff_type = self._classify_diff(added_lines, removed_lines)

        return {
            "identical": False,
            "diff_type": diff_type,
            "line_changes": changed_count,
            "added_lines": added_lines,
            "removed_lines": removed_lines,
        }

    # ── LLM 摘要 ─────────────────────────────────

    async def summarize_diff(
        self, original: str, revised: str, diff: dict
    ) -> str:
        """用 LLM 生成人类可读的对比摘要"""
        if not self.llm:
            return self._fallback_summary(diff)

        prompt = (
            "你是文档对比专家。以下是两个版本文档的差异，请用一句话总结变更内容。\n\n"
            f"【原版】\n{original}\n\n"
            f"【新版】\n{revised}\n\n"
            f"差异类型：{diff['diff_type']}\n"
            f"新增行：{diff.get('added_lines', [])}\n"
            f"删除行：{diff.get('removed_lines', [])}\n\n"
            "总结："
        )
        return await self.llm.generate(prompt)

    # ── 辅助方法 ─────────────────────────────────

    def _no_diff(self) -> dict:
        return {
            "identical": True,
            "diff_type": "无变化",
            "line_changes": 0,
            "added_lines": [],
            "removed_lines": [],
        }

    def _all_added(self, text: str) -> dict:
        lines = text.splitlines()
        return {
            "identical": False,
            "diff_type": "新增",
            "line_changes": len(lines),
            "added_lines": lines,
            "removed_lines": [],
        }

    def _all_removed(self, text: str) -> dict:
        lines = text.splitlines()
        return {
            "identical": False,
            "diff_type": "删除",
            "line_changes": len(lines),
            "added_lines": [],
            "removed_lines": lines,
        }

    @staticmethod
    def _classify_diff(added: list, removed: list) -> str:
        if added and not removed:
            return "新增"
        if removed and not added:
            return "删除"
        return "修改"

    @staticmethod
    def _fallback_summary(diff: dict) -> str:
        """无 LLM 时的兜底摘要"""
        return (
            f"文档对比结果：{diff['diff_type']}，"
            f"共 {diff['line_changes']} 处变更。"
        )
