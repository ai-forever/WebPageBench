"""Parse the OpenCUA / EvoCUA-S1 markdown-sections response format."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from bench_eval.agents.core.actions import Action
from bench_eval.agents.core.coordinates import CoordinateScaler
from bench_eval.agents.core.parsers import extract_code_blocks, parse_pyautogui_code

_SECTION_PATTERNS = {
    "observation": r"#{1,3}\s*Observation\s*:?[\n\r]+(.*?)(?=^#{1,3}\s|\Z)",
    "thought": r"#{1,3}\s*Thought\s*:?[\n\r]+(.*?)(?=^#{1,3}\s|\Z)",
    "action": r"#{1,3}\s*Action\s*:?[\n\r]+(.*?)(?=^#{1,3}\s|\Z)",
}


@dataclass
class ParsedSections:
    observation: Optional[str] = None
    thought: Optional[str] = None
    action: Optional[str] = None
    code: Optional[str] = None
    actions: list[Action] = field(default_factory=list)
    error: Optional[str] = None

    def as_metadata(self) -> dict:
        return {
            key: value
            for key, value in (
                ("observation", self.observation),
                ("thought", self.thought),
                ("action", self.action),
                ("code", self.code),
                ("error", self.error),
            )
            if value
        }


def parse_response(response: str, scaler: CoordinateScaler) -> ParsedSections:
    sections = ParsedSections()
    text = response or ""

    for key, pattern in _SECTION_PATTERNS.items():
        match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
        if match:
            value = match.group(1).strip()
            # A "## Code:" block belongs to the code section, not the prose above it.
            setattr(sections, key, value.split("## Code")[0].strip() or None)

    blocks = extract_code_blocks(text)
    if not blocks:
        sections.error = "no code block in response"
        return sections

    sections.code = blocks[-1]
    sections.actions = parse_pyautogui_code(sections.code, scaler)
    if not sections.actions:
        sections.error = f"no executable action parsed from: {sections.code[:200]}"
    return sections
