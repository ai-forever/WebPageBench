"""Qwen3-VL computer-use prompts, adapted from the desktop wording to the browser.

The tool schema is kept byte-compatible with the one Qwen3-VL was trained on —
only the environment description mentions a browser viewport instead of an Ubuntu
desktop. Changing the schema itself measurably degrades grounding.
"""

from __future__ import annotations

import json

ACTION_DESCRIPTION = """
* `key`: Performs key down presses on the arguments passed in order, then performs key releases in reverse order.
* `type`: Type a string of text on the keyboard.
* `mouse_move`: Move the cursor to a specified (x, y) pixel coordinate on the screen.
* `left_click`: Click the left mouse button at a specified (x, y) pixel coordinate on the screen.
* `left_click_drag`: Click and drag the cursor to a specified (x, y) pixel coordinate on the screen.
* `right_click`: Click the right mouse button at a specified (x, y) pixel coordinate on the screen.
* `middle_click`: Click the middle mouse button at a specified (x, y) pixel coordinate on the screen.
* `double_click`: Double-click the left mouse button at a specified (x, y) pixel coordinate on the screen.
* `scroll`: Performs a scroll of the mouse scroll wheel.
* `wait`: Wait specified seconds for the change to happen.
* `terminate`: Terminate the current task and report its completion status.
"""

ENVIRONMENT_LINES = [
    "Use a mouse and keyboard to interact with a web browser, and take screenshots.",
    "* This is a web application rendered in a browser viewport. There is no desktop, terminal, or application menu — everything you need is on the page.",
    "* Pages are single-page applications: after a click the content may take a moment to update, so you may need to wait and take another screenshot to see the result.",
    "* Scroll the page when the element you need is not visible in the current viewport.",
    "* Whenever you intend to move the cursor to click on an element, first consult the screenshot to determine its coordinates.",
    "* If you clicked something but nothing happened even after waiting, adjust the cursor position so it visually falls on the element.",
    "* Click buttons, links and icons with the cursor tip in the center of the element. Don't click boxes on their edges unless asked.",
]

RESOLUTION_ABSOLUTE = "* The screen's resolution is {width}x{height}."
RESOLUTION_RELATIVE = "* The screen's resolution is 1000x1000."

SYSTEM_PROMPT = """# Tools

You may call one or more functions to assist with the user query.

You are provided with function signatures within <tools></tools> XML tags:
<tools>
{tools}
</tools>

For each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:
<tool_call>
{{"name": <function-name>, "arguments": <args-json-object>}}
</tool_call>

# Response format

Response format for every step:
1) Action: a short imperative describing what to do in the UI.
2) A single <tool_call>...</tool_call> block containing only the JSON: {{"name": <function-name>, "arguments": <args-json-object>}}.

Rules:
- Output exactly in the order: Action, <tool_call>.
- Be brief: one sentence for Action.
- Do not output anything else outside those parts.
- If finishing, use action=terminate in the tool call."""

INSTRUCTION_PROMPT = """
Please generate the next move according to the UI screenshot, instruction and previous actions.

Instruction: {instruction}

Previous actions:
{previous_actions}"""


def build_tools_definition(*, width: int, height: int, absolute: bool) -> dict:
    """The `computer_use` tool schema Qwen3-VL expects in its system prompt."""
    lines = list(ENVIRONMENT_LINES)
    resolution = (
        RESOLUTION_ABSOLUTE.format(width=width, height=height)
        if absolute
        else RESOLUTION_RELATIVE
    )
    lines.insert(3, resolution)
    return {
        "type": "function",
        "function": {
            "name_for_human": "computer_use",
            "name": "computer_use",
            "description": "\n".join(lines),
            "parameters": {
                "properties": {
                    "action": {
                        "description": ACTION_DESCRIPTION,
                        "enum": [
                            "key",
                            "type",
                            "mouse_move",
                            "left_click",
                            "left_click_drag",
                            "right_click",
                            "middle_click",
                            "double_click",
                            "scroll",
                            "wait",
                            "terminate",
                        ],
                        "type": "string",
                    },
                    "keys": {"description": "Required only by `action=key`.", "type": "array"},
                    "text": {"description": "Required only by `action=type`.", "type": "string"},
                    "coordinate": {
                        "description": "The x,y coordinates for mouse actions.",
                        "type": "array",
                    },
                    "pixels": {"description": "The amount of scrolling.", "type": "number"},
                    "time": {"description": "The seconds to wait.", "type": "number"},
                    "status": {
                        "description": "The status of the task.",
                        "type": "string",
                        "enum": ["success", "failure"],
                    },
                },
                "required": ["action"],
                "type": "object",
            },
            "args_format": "Format the arguments as a JSON object.",
        },
    }


def build_system_prompt(*, width: int, height: int, absolute: bool) -> str:
    tools = build_tools_definition(width=width, height=height, absolute=absolute)
    return SYSTEM_PROMPT.format(tools=json.dumps(tools))
