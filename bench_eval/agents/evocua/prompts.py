"""EvoCUA prompts for both prompt styles.

* **S1** — OpenCUA-style markdown sections with a pyautogui code block.
* **S2** — Qwen3-VL-style `computer_use` tool calls, with `triple_click`,
  `key_down` and `key_up` added to the enum.

Both are adapted from desktop wording to the browser viewport the bench renders.
"""

from __future__ import annotations

import json

# ---------------------------------------------------------------- S1 (code)

S1_SYSTEM_PROMPT = """You are a GUI agent. You are given a task, a screenshot of a browser viewport and your previous interactions with the page. You need to perform a series of actions to complete the task. The screen shows a web application: there is no desktop or terminal, everything you need is inside the page. You need to **wait** explicitly when the page is loading or a request is in flight. Don't terminate the task unless you are sure the task is finished. If you find that you can't finish the task, or the task is not finished exactly as the instruction indicates, or the task is impossible to complete, you must report **failure**.

For each step, provide your response in this format:
# Step: {{step number}}
## Thought:
{{thought}}
## Action:
{{action}}
## Code:
{{code}}

For the Thought section, you should include the following parts:
- Reflection on the previous action and its outcome, if there was one
- Step by step progress assessment: what is already done, and the plan for the rest
- Next action prediction with the reason
- For text input actions: the current cursor position, consolidated repetitive keypresses, and the expected final text
- Use first-person perspective in reasoning

For the Action section, provide a clear, concise and actionable instruction in one sentence:
- Describe the target explicitly without using coordinates; distinguish it when several elements share a name
- Describe features (shape, color, position) when the name is unavailable
- For keyboard actions, consolidate repetitive keypresses with a count and state the expected text outcome

For the Code section, output the corresponding code for the action. The code should be either PyAutoGUI code or one of the following functions wrapped in a code block:
- {{"name": "computer.wait", "description": "Wait for the page to load or a request to finish", "parameters": {{"type": "object", "properties": {{}}, "required": []}}}}
- {{"name": "computer.triple_click", "description": "Triple click on the screen", "parameters": {{"type": "object", "properties": {{"x": {{"type": "number"}}, "y": {{"type": "number"}}}}, "required": ["x", "y"]}}}}
- {{"name": "computer.terminate", "description": "Terminate the current task and report its completion status", "parameters": {{"type": "object", "properties": {{"status": {{"type": "string", "enum": ["success", "failure"]}}, "answer": {{"type": "string"}}}}, "required": ["status"]}}}}
Examples for the code section:
```python
pyautogui.click(x=0.5, y=0.42)
```
```python
computer.terminate(status='success')
```"""

S1_INSTRUCTION_TEMPLATE = (
    "# Task Instruction:\n{instruction}\n\n"
    "Please generate the next move according to the screenshot, task instruction "
    "and previous steps (if provided).\n"
)

S1_STEP_TEMPLATE = "# Step {step_num}:\n"
S1_HISTORY_TEMPLATE = "## Thought:\n{thought}\n\n## Action:\n{action}\n"

# ------------------------------------------------------------ S2 (tool call)

S2_ACTION_DESCRIPTION = """
* `key`: Performs key down presses on the arguments passed in order, then performs key releases in reverse order.
* `type`: Type a string of text on the keyboard.
* `mouse_move`: Move the cursor to a specified (x, y) pixel coordinate on the screen.
* `left_click`: Click the left mouse button at a specified (x, y) pixel coordinate on the screen.
* `left_click_drag`: Click and drag the cursor to a specified (x, y) pixel coordinate on the screen.
* `right_click`: Click the right mouse button at a specified (x, y) pixel coordinate on the screen.
* `middle_click`: Click the middle mouse button at a specified (x, y) pixel coordinate on the screen.
* `double_click`: Double-click the left mouse button at a specified (x, y) pixel coordinate on the screen.
* `triple_click`: Triple-click the left mouse button at a specified (x, y) pixel coordinate on the screen.
* `scroll`: Performs a scroll of the mouse scroll wheel.
* `wait`: Wait specified seconds for the change to happen.
* `terminate`: Terminate the current task and report its completion status.
* `key_down`: Press and hold a key.
* `key_up`: Release a held key.
"""

S2_DESCRIPTION_PROMPT_TEMPLATE = """Use a mouse and keyboard to interact with a web browser, and take screenshots.
* This is a web application rendered in a browser viewport. There is no desktop or terminal — everything you need is on the page.
* Pages are single-page applications: after a click the content may take a moment to update, so you may need to wait and take another screenshot to see the result.
{resolution_info}
* Scroll the page when the element you need is not visible in the current viewport.
* Whenever you intend to move the cursor to click on an element, first consult the screenshot to determine its coordinates.
* If you clicked something but nothing happened even after waiting, adjust the cursor position so it visually falls on the element.
* Make sure to click any buttons, links and icons with the cursor tip in the center of the element. Don't click boxes on their edges unless asked."""

S2_SYSTEM_PROMPT = """# Tools

You may call one or more functions to assist with the user query.

You are provided with function signatures within <tools></tools> XML tags:
<tools>
{tools_xml}
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

S2_INSTRUCTION_TEMPLATE = """
Please generate the next move according to the UI screenshot, instruction and previous actions.

Instruction: {instruction}

Previous actions:
{previous_actions}"""


def build_s2_tools_definition(description_prompt: str) -> dict:
    return {
        "type": "function",
        "function": {
            "name_for_human": "computer_use",
            "name": "computer_use",
            "description": description_prompt,
            "parameters": {
                "properties": {
                    "action": {
                        "description": S2_ACTION_DESCRIPTION,
                        "enum": [
                            "key",
                            "type",
                            "mouse_move",
                            "left_click",
                            "left_click_drag",
                            "right_click",
                            "middle_click",
                            "double_click",
                            "triple_click",
                            "scroll",
                            "wait",
                            "terminate",
                            "key_down",
                            "key_up",
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


def build_s2_system_prompt(*, width: int, height: int, absolute: bool) -> str:
    resolution_info = (
        f"* The screen's resolution is {width}x{height}."
        if absolute
        else "* The screen's resolution is 1000x1000."
    )
    description = S2_DESCRIPTION_PROMPT_TEMPLATE.format(resolution_info=resolution_info)
    tools = build_s2_tools_definition(description)
    return S2_SYSTEM_PROMPT.format(tools_xml=json.dumps(tools))
