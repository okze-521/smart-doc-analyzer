"""LLM 异步客户端 — 支持本地 Ollama / DeepSeek API"""

import json

import httpx
import httpcore


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

    # ── 连接错误类型（用于 fallback 判断） ──
    _CONNECT_ERRORS = (
        httpx.ConnectError, httpx.TimeoutException, httpx.RemoteProtocolError,
        httpcore.ConnectError, httpcore.ReadError, httpcore.WriteError,
    )

    async def generate_with_context(
        self, query: str, context_chunks: list[str], history: list[dict[str, str]] | None = None
    ) -> str:
        """带上下文的 RAG 生成，支持多轮对话历史 + 自动 fallback"""
        system_prompt = self.build_rag_prompt(query, context_chunks)
        try:
            return await self._primary_chat(system_prompt, query, history)
        except self._CONNECT_ERRORS:
            if self._can_fallback():
                return await self._deepseek_chat(system_prompt, query, history)
            raise

    async def generate_with_context_stream(
        self, query: str, context_chunks: list[str], history: list[dict[str, str]] | None = None
    ):
        """流式 RAG 生成，支持自动 fallback"""
        system_prompt = self.build_rag_prompt(query, context_chunks)
        messages = self._build_messages(system_prompt, query, history)
        try:
            gen = self._primary_chat_stream(messages)
            async for token in gen:
                yield token
        except self._CONNECT_ERRORS:
            if self._can_fallback():
                async for token in self._deepseek_chat_stream(messages):
                    yield token
            else:
                raise

    # ── Provider 路由 ─────────────────────

    def _can_fallback(self) -> bool:
        """检查是否有备用的 DeepSeek API"""
        return self.provider == "ollama" and bool(self.deepseek_api_key)

    async def _primary_chat(self, system: str, user: str, history: list[dict[str, str]] | None) -> str:
        """路由到当前主 provider 的聊天"""
        if self.provider == "ollama":
            return await self._ollama_chat(system, user, history)
        return await self._deepseek_chat(system, user, history)

    async def _primary_chat_stream(self, messages: list[dict[str, str]]):
        """路由到当前主 provider 的流式聊天"""
        if self.provider == "ollama":
            async for token in self._ollama_chat_stream(messages):
                yield token
        else:
            async for token in self._deepseek_chat_stream(messages):
                yield token

    # ── Ollama 后端 ─────────────────────

    async def _ollama_generate(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=httpx.Timeout(300)) as client:
            resp = await client.post(
                f"{self.ollama_host}/api/generate",
                json={"model": self.ollama_model, "prompt": prompt, "stream": False},
            )
            resp.raise_for_status()
            return resp.json()["response"]

    async def _ollama_chat(self, system: str, user: str, history: list[dict[str, str]] | None = None) -> str:
        messages = self._build_messages(system, user, history)
        async with httpx.AsyncClient(timeout=httpx.Timeout(300)) as client:
            resp = await client.post(
                f"{self.ollama_host}/api/chat",
                json={"model": self.ollama_model, "messages": messages, "stream": False},
            )
            resp.raise_for_status()
            return resp.json()["message"]["content"]

    async def _ollama_chat_stream(self, messages: list[dict[str, str]]):
        """Ollama 流式聊天，yield token"""
        async with httpx.AsyncClient(timeout=httpx.Timeout(300)) as client:
            async with client.stream(
                "POST",
                f"{self.ollama_host}/api/chat",
                json={"model": self.ollama_model, "messages": messages, "stream": True},
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line:
                        continue
                    try:
                        chunk = json.loads(line)
                        content = chunk.get("message", {}).get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        continue

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

    async def _deepseek_chat(self, system: str, user: str, history: list[dict[str, str]] | None = None) -> str:
        messages = self._build_messages(system, user, history)
        async with httpx.AsyncClient(timeout=httpx.Timeout(120)) as client:
            resp = await client.post(
                f"{self.DEEPSEEK_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {self.deepseek_api_key}"},
                json={"model": self.DEEPSEEK_MODEL, "messages": messages},
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def _deepseek_chat_stream(self, messages: list[dict[str, str]]):
        """DeepSeek 流式聊天，yield token（SSE 格式）"""
        async with httpx.AsyncClient(timeout=httpx.Timeout(120)) as client:
            async with client.stream(
                "POST",
                f"{self.DEEPSEEK_BASE}/chat/completions",
                headers={"Authorization": f"Bearer {self.deepseek_api_key}"},
                json={"model": self.DEEPSEEK_MODEL, "messages": messages, "stream": True},
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data: "):
                        continue
                    data = line[6:]  # 去掉 "data: " 前缀
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                        content = chunk["choices"][0].get("delta", {}).get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue

    # ── 工具方法 ────────────────────────

    @staticmethod
    def _build_messages(system: str, user: str, history: list[dict[str, str]] | None) -> list[dict[str, str]]:
        """构建 messages 列表：system + 历史 + 当前用户消息"""
        messages = [{"role": "system", "content": system}]
        if history:
            for msg in history[-20:]:
                if msg.get("role") in ("user", "assistant"):
                    messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user})
        return messages

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
