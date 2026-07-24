"""LLM 异步客户端 — 支持本地 Ollama / DeepSeek API"""

import httpx


class LLMClient:
    """统一 LLM 接口，通过 LLM_PROVIDER 切换后端"""

    def __init__(
        self,
        provider: str | None = None,
        ollama_host: str | None = None,
        ollama_model: str | None = None,
        deepseek_api_key: str | None = None,
    ):
        from src.config import settings
        self.provider = provider or settings.LLM_PROVIDER
        self.ollama_host = ollama_host or settings.OLLAMA_HOST
        self.ollama_model = ollama_model or settings.OLLAMA_MODEL
        self.deepseek_api_key = deepseek_api_key or settings.DEEPSEEK_API_KEY

    # ── 公开接口 ────────────────────────

    async def generate(self, prompt: str) -> str:
        """基础文本生成"""
        if self.provider == "ollama":
            return await self._ollama_generate(prompt)
        else:
            return await self._deepseek_generate(prompt)

    async def generate_with_context(
        self, query: str, context_chunks: list[str]
    ) -> str:
        """带上下文的 RAG 生成"""
        system_prompt = self.build_rag_prompt(query, context_chunks)
        if self.provider == "ollama":
            return await self._ollama_chat(system_prompt, query)
        else:
            return await self._deepseek_chat(system_prompt, query)

    # ── Ollama 后端 ─────────────────────

    async def _ollama_generate(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=httpx.Timeout(300)) as client:
            resp = await client.post(
                f"{self.ollama_host}/api/generate",
                json={"model": self.ollama_model, "prompt": prompt, "stream": False},
            )
            resp.raise_for_status()
            return resp.json()["response"]

    async def _ollama_chat(self, system: str, user: str) -> str:
        async with httpx.AsyncClient(timeout=httpx.Timeout(300)) as client:
            resp = await client.post(
                f"{self.ollama_host}/api/chat",
                json={
                    "model": self.ollama_model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "stream": False,
                },
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"]

    # ── DeepSeek 后端 ───────────────────

    DEEPSEEK_BASE = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL = "deepseek-chat"

    async def _deepseek_generate(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120)) as client:
            resp = await client.post(
                f"{self.DEEPSEEK_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {self.deepseek_api_key}"},
                json={
                    "model": self.DEEPSEEK_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def _deepseek_chat(self, system: str, user: str) -> str:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120)) as client:
            resp = await client.post(
                f"{self.DEEPSEEK_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {self.deepseek_api_key}"},
                json={
                    "model": self.DEEPSEEK_MODEL,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                },
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    # ── 工具方法 ────────────────────────

    @staticmethod
    def build_rag_prompt(query: str, context_chunks: list[str]) -> str:
        """构建 RAG 系统提示词"""
        context = "\n---\n".join(context_chunks)
        return (
            "你是一个文档问答助手。请严格根据以下文档内容回答问题。\n"
            "如果文档中没有相关信息，直接说「未找到相关信息」。\n"
            "不要编造内容。\n\n"
            f"## 文档片段\n{context}\n\n"
            f"## 问题\n{query}"
        )
