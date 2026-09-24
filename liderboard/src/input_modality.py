"""What the harness actually sends to the model in this bench."""

from __future__ import annotations

IMAGE_HARNESSES = frozenset({"qwen3-vl", "uitars", "jedi", "opencua", "evocua", "fara"})
TEXT_HARNESSES = frozenset({"openhands"})
TEXT_IMAGE_HARNESSES = frozenset(
    {
        "browser-use",
        "openmanus",
        "ouroboros-cut",
        "ouroboros-full-isolated",
        "ouroboros-full-evolving",
    }
)
TEXT_ONLY_MODELS = frozenset({"z-ai/glm-5.2", "minimax/minimax-m2.7"})
# browser-use / openmanus in this bench drop vision for DeepSeek — LLM sees DOM only.
DOM_TEXT_EVEN_IF_VISION_HARNESS = frozenset({"deepseek/deepseek-v4.1-flash"})

INPUT_HELP = (
    "Harness input: text (DOM/text only), text+image (page text plus screenshots), "
    "or image (GUI screenshot, no DOM). DeepSeek on browser-use/openmanus is DOM-only. "
    "Text-only models on Ouroboros do not get a screenshot injected into the LLM."
)


def harness_input(model: str | None, harness: str | None) -> str:
    if not harness:
        return "—"
    if harness in IMAGE_HARNESSES:
        return "image"
    if harness in TEXT_HARNESSES:
        return "text"
    if harness in TEXT_IMAGE_HARNESSES:
        if model in TEXT_ONLY_MODELS:
            return "text"
        if model in DOM_TEXT_EVEN_IF_VISION_HARNESS and harness in {"browser-use", "openmanus"}:
            return "text"
        return "text+image"
    return "—"
