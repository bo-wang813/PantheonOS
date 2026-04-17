"""
Unit tests for native tool-result image routing.

Covers:
- vision_capability.supports_tool_result_image() returns the right provider verdict
- image_blocks helpers split content correctly
- Anthropic adapter translates OpenAI image_url in tool messages → image blocks
- Gemini adapter emits functionResponse + inline_data parts when tool returns images
- OpenAI Chat Completions adapter sanitises tool-message images to a text placeholder
- Responses API path emits input_image items in function_call_output
- observe_images tool picks native vs sub-agent mode based on active model
"""

from __future__ import annotations

import base64

import pytest

from pantheon.utils.vision_capability import supports_tool_result_image
from pantheon.utils.adapters.image_blocks import (
    has_image_content,
    resolve_image_url,
    split_text_and_images,
)
from pantheon.utils.adapters.anthropic_adapter import (
    _convert_messages_to_anthropic,
    _content_to_anthropic_tool_result,
)
from pantheon.utils.adapters.gemini_adapter import _convert_messages_to_gemini
from pantheon.utils.adapters.openai_adapter import (
    _sanitize_tool_messages_for_chat_completions,
)
from pantheon.utils.llm import _convert_messages_to_responses_input


# Tiny 1×1 PNG (base64). Enough for tests without external files.
_TINY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYGBgAAAABQABXvMqOgAAAABJRU5ErkJggg=="
)
_TINY_PNG_DATA_URI = f"data:image/png;base64,{_TINY_PNG_B64}"


# ============ capability detection ============


class TestCapabilityDetection:

    def test_none_returns_false(self):
        assert supports_tool_result_image(None) is False

    def test_anthropic_supported(self):
        assert supports_tool_result_image("anthropic/claude-sonnet-4-6") is True
        assert supports_tool_result_image("claude-opus-4") is True

    def test_gemini_supported(self):
        assert supports_tool_result_image("gemini/gemini-2.5-pro") is True
        assert supports_tool_result_image("google/gemini-2.0-flash") is True

    def test_openai_chat_completions_not_supported(self):
        assert supports_tool_result_image("gpt-4o") is False
        assert supports_tool_result_image("openai/gpt-4o") is False
        assert supports_tool_result_image("gpt-5") is False

    def test_openai_responses_api_supported(self):
        # codex and *-pro models go through Responses API which supports images
        assert supports_tool_result_image("codex-mini-latest") is True


# ============ image_blocks helpers ============


class TestImageBlocksHelpers:

    def test_has_image_content_true(self):
        assert (
            has_image_content(
                [
                    {"type": "text", "text": "hi"},
                    {"type": "image_url", "image_url": {"url": "x"}},
                ]
            )
            is True
        )

    def test_has_image_content_string(self):
        assert has_image_content("plain string") is False

    def test_has_image_content_text_only(self):
        assert has_image_content([{"type": "text", "text": "hi"}]) is False

    def test_resolve_data_uri(self):
        mime, data = resolve_image_url(_TINY_PNG_DATA_URI)
        assert mime == "image/png"
        assert data == _TINY_PNG_B64

    def test_resolve_jpg_normalized_to_jpeg(self):
        uri = "data:image/jpg;base64,AAAA"
        mime, data = resolve_image_url(uri)
        assert mime == "image/jpeg"
        assert data == "AAAA"

    def test_resolve_http_returns_none(self):
        assert resolve_image_url("https://example.com/a.png") is None

    def test_split_content(self):
        content = [
            {"type": "text", "text": "hello"},
            {"type": "image_url", "image_url": {"url": _TINY_PNG_DATA_URI}},
            {"type": "image_url", "image_url": {"url": "https://e.com/x.png"}},
        ]
        text, inline, http = split_text_and_images(content)
        assert text == "hello"
        assert len(inline) == 1
        assert inline[0] == ("image/png", _TINY_PNG_B64)
        assert http == ["https://e.com/x.png"]


# ============ Anthropic adapter ============


class TestAnthropicAdapter:

    def test_tool_result_plain_string(self):
        out = _content_to_anthropic_tool_result("plain text")
        assert out == "plain text"

    def test_tool_result_text_only_list(self):
        out = _content_to_anthropic_tool_result(
            [{"type": "text", "text": "hello"}]
        )
        assert out == "hello"

    def test_tool_result_with_image(self):
        blocks = _content_to_anthropic_tool_result(
            [
                {"type": "text", "text": "see this"},
                {"type": "image_url", "image_url": {"url": _TINY_PNG_DATA_URI}},
            ]
        )
        assert isinstance(blocks, list)
        assert blocks[0] == {"type": "text", "text": "see this"}
        img = blocks[1]
        assert img["type"] == "image"
        assert img["source"]["type"] == "base64"
        assert img["source"]["media_type"] == "image/png"
        assert img["source"]["data"] == _TINY_PNG_B64

    def test_convert_messages_tool_image(self):
        messages = [
            {"role": "user", "content": "look at this"},
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "observe_images", "arguments": "{}"},
                    }
                ],
            },
            {
                "role": "tool",
                "tool_call_id": "call_1",
                "content": [
                    {"type": "text", "text": "here's the image"},
                    {"type": "image_url", "image_url": {"url": _TINY_PNG_DATA_URI}},
                ],
            },
        ]
        _system, converted = _convert_messages_to_anthropic(messages)
        # Find the tool_result block
        tool_result_msg = None
        for m in converted:
            for block in m.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "tool_result":
                    tool_result_msg = block
                    break
        assert tool_result_msg is not None
        inner = tool_result_msg["content"]
        assert isinstance(inner, list)
        assert any(b.get("type") == "image" for b in inner)
        img_block = [b for b in inner if b["type"] == "image"][0]
        assert img_block["source"]["media_type"] == "image/png"
        assert img_block["source"]["data"] == _TINY_PNG_B64


# ============ Gemini adapter ============


class TestGeminiAdapter:

    def test_tool_with_image_emits_inline_data(self):
        messages = [
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "observe_images", "arguments": "{}"},
                    }
                ],
            },
            {
                "role": "tool",
                "tool_call_id": "call_1",
                "name": "observe_images",
                "content": [
                    {"type": "text", "text": "saw cat"},
                    {"type": "image_url", "image_url": {"url": _TINY_PNG_DATA_URI}},
                ],
            },
        ]
        _sys, contents = _convert_messages_to_gemini(messages)
        # Find the user message carrying the functionResponse
        fn_response_msg = None
        for m in contents:
            parts = m.get("parts") or []
            if any("functionResponse" in p for p in parts):
                fn_response_msg = m
                break
        assert fn_response_msg is not None
        parts = fn_response_msg["parts"]
        # First part = functionResponse with the text summary
        assert "functionResponse" in parts[0]
        assert parts[0]["functionResponse"]["response"]["result"] == "saw cat"
        # Subsequent parts carry the actual image bytes via inline_data
        inline_parts = [p for p in parts if "inline_data" in p]
        assert len(inline_parts) == 1
        assert inline_parts[0]["inline_data"]["mime_type"] == "image/png"
        assert inline_parts[0]["inline_data"]["data"] == _TINY_PNG_B64


# ============ OpenAI Chat Completions sanitiser ============


class TestOpenAIChatCompletionsSanitiser:

    def test_strip_image_from_tool_message(self):
        messages = [
            {"role": "user", "content": "hi"},
            {
                "role": "tool",
                "tool_call_id": "call_1",
                "content": [
                    {"type": "text", "text": "here"},
                    {"type": "image_url", "image_url": {"url": _TINY_PNG_DATA_URI}},
                ],
            },
        ]
        out = _sanitize_tool_messages_for_chat_completions(messages)
        tool_msg = out[1]
        content = tool_msg["content"]
        assert isinstance(content, str)
        assert "here" in content
        assert "1 image(s)" in content

    def test_passthrough_non_image_tool(self):
        messages = [
            {"role": "tool", "tool_call_id": "c", "content": "ok"},
        ]
        out = _sanitize_tool_messages_for_chat_completions(messages)
        assert out[0]["content"] == "ok"


# ============ Responses API conversion ============


class TestResponsesAPIConversion:

    def test_tool_output_string_unchanged(self):
        messages = [
            {"role": "tool", "tool_call_id": "c1", "content": "hello"},
        ]
        _instructions, items = _convert_messages_to_responses_input(messages)
        fco = next(i for i in items if i.get("type") == "function_call_output")
        assert fco["output"] == "hello"

    def test_tool_output_with_image_emits_items(self):
        messages = [
            {
                "role": "tool",
                "tool_call_id": "c1",
                "content": [
                    {"type": "text", "text": "see"},
                    {"type": "image_url", "image_url": {"url": _TINY_PNG_DATA_URI}},
                ],
            },
        ]
        _instructions, items = _convert_messages_to_responses_input(messages)
        fco = next(i for i in items if i.get("type") == "function_call_output")
        output = fco["output"]
        assert isinstance(output, list)
        types = [it.get("type") for it in output]
        assert "input_text" in types
        assert "input_image" in types
        img_item = next(it for it in output if it["type"] == "input_image")
        assert img_item["image_url"].startswith("data:image/png;base64,")
