"""LLM 客户端测试 — mock DeepSeek API"""

import pytest
import httpx
from unittest.mock import patch, AsyncMock


class MockResponse:
    """模拟 httpx.Response"""
    def __init__(self, json_data, status_code=200):
        self._json = json_data
        self.status_code = status_code

    def json(self):
        return self._json

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=self)


@pytest.fixture
def mock_post():
    """mock httpx.AsyncClient.post"""
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as m:
        m.return_value = MockResponse({
            "choices": [{"message": {"content": "这是一个模拟回答"}}]
        })
        yield m


@pytest.fixture
def client():
    """测试用 LLM 客户端 — 假 Key（http 已 mock）"""
    from src.core.llm_client import LLMClient
    return LLMClient(provider="deepseek", deepseek_api_key="fake-test-key")


class TestLLMClientBasic:
    """基础调用"""

    def test_generate_returns_string(self, client, mock_post):
        import asyncio
        result = asyncio.run(client.generate("你好"))
        assert isinstance(result, str)
        assert result == "这是一个模拟回答"

    def test_prompt_sent_as_user_message(self, client, mock_post):
        import asyncio
        asyncio.run(client.generate("测试问题"))
        call_args = mock_post.call_args
        sent_json = call_args.kwargs["json"]
        assert sent_json["messages"][0]["role"] == "user"
        assert sent_json["messages"][0]["content"] == "测试问题"

    def test_model_and_url_sent(self, client, mock_post):
        import asyncio
        asyncio.run(client.generate("hi"))
        call_args = mock_post.call_args
        assert "/chat/completions" in call_args.args[0]
        sent_json = call_args.kwargs["json"]
        assert sent_json["model"] == "deepseek-chat"


class TestLLMClientContext:
    """上下文注入"""

    def test_generate_with_context(self, client, mock_post):
        import asyncio
        context = ["文档片段1：合同金额500万", "文档片段2：签订日期2026-07-24"]
        asyncio.run(client.generate_with_context(
            query="合同金额是多少？",
            context_chunks=context,
        ))
        sent_json = mock_post.call_args.kwargs["json"]
        messages = sent_json["messages"]
        assert messages[0]["role"] == "system"
        assert "文档片段1" in messages[0]["content"]
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "合同金额是多少？"

    def test_build_rag_prompt(self, client):
        chunks = ["文档A：销售额100万", "文档B：利润20万"]
        prompt = client.build_rag_prompt("销售额多少？", chunks)
        assert "文档A：销售额100万" in prompt
        assert "文档B：利润20万" in prompt
        assert "销售额多少？" in prompt

    def test_remove_key_validation_on_init(self):
        """__init__ 不应校验 Key（允许环境变量不存在）"""
        from src.core.llm_client import LLMClient
        import os
        # 不应该抛异常
        c = LLMClient(provider="deepseek", deepseek_api_key="any")
        assert c.deepseek_api_key == "any"


class TestLLMClientErrors:
    """错误处理"""

    def test_api_error_raises_exception(self, client, mock_post):
        import asyncio
        mock_post.return_value = MockResponse(
            {"error": "invalid api key"}, status_code=401
        )
        with pytest.raises(httpx.HTTPStatusError):
            asyncio.run(client.generate("test"))

    def test_network_timeout(self, client, mock_post):
        import asyncio
        mock_post.side_effect = httpx.ConnectTimeout("timeout")
        with pytest.raises(httpx.ConnectTimeout):
            asyncio.run(client.generate("test"))
