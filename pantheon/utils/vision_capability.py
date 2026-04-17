"""
Vision capability detection for LLM providers.

Determines which providers/models support embedding images directly in
tool result messages (native mode) vs. requiring a sub-agent to view
images and return a text summary (fallback mode).

Native support map (as of 2026-04):
- Anthropic Messages API: tool_result.content can contain image blocks
- Gemini API: functionResponse parts can carry inline_data (image)
- OpenAI Responses API: function_call_output can include input_image items
- OpenAI Chat Completions: NOT supported (tool role cannot carry image_url)
- Other OpenAI-compatible providers via Chat Completions: NOT supported
"""

from __future__ import annotations

from .llm_providers import ProviderType, detect_provider, is_responses_api_model


def supports_tool_result_image(model: str | None) -> bool:
    """Return True when the provider can accept image content in tool messages.

    Args:
        model: Model string (e.g. "anthropic/claude-sonnet-4-6", "gpt-4o",
               "gemini/gemini-2.5-pro"). None → False (conservative).

    Returns:
        True  → tool can return {type:"image_url", ...} and it will reach
                the model natively.
        False → images in tool messages will be stripped. Caller should
                fall back to sub-agent pattern (observe-style).
    """
    if not model:
        return False

    bare = model.lower()
    # Strip provider prefix for matching (e.g. "anthropic/claude" → "claude")
    if "/" in bare:
        prefix, tail = bare.split("/", 1)
    else:
        prefix, tail = "", bare

    # Explicit native SDK providers that support image in tool result.
    if prefix in {"anthropic", "claude"}:
        return True
    if prefix in {"gemini", "google"}:
        return True
    # Bare model names without provider prefix.
    if not prefix:
        if tail.startswith("claude") or tail.startswith("gemini"):
            return True

    # OpenAI Responses API supports input_image in function_call_output.
    # Use the existing helper to detect Responses-only models (codex, *-pro, etc.).
    try:
        config = detect_provider(model, relaxed_schema=False)
        if config.provider_type == ProviderType.NATIVE:
            # Any NATIVE-routed model with recognised prefix handled above;
            # otherwise default conservative.
            bare_model = config.model_name.lower()
            if bare_model.startswith(("anthropic/", "claude", "gemini", "google/")):
                return True
            return False
        if is_responses_api_model(config):
            return True
    except Exception:
        # Fall through to False on any detection failure.
        pass

    return False


__all__ = ["supports_tool_result_image"]
