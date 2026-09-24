"""Jedi prompts: a planner that writes pyautogui, and a grounder that locates elements.

The planner never has to be accurate about coordinates — it describes the target
in a `#` comment and puts a placeholder in the call. The Jedi VL model then
resolves that description to a real pixel on the current screenshot.
"""

from __future__ import annotations

import json

GROUNDER_TOOLS = {
    "type": "function",
    "function": {
        "name": "computer_use",
        "description": (
            "Use a mouse and keyboard to interact with a web browser, and take screenshots.\n"
            "* This is a web application rendered in a browser viewport. Everything you need is on the page.\n"
            "* Some interactions take time to apply, so you may need to wait and take another screenshot.\n"
            "* The screen's resolution is {width}x{height}.\n"
            "* Whenever you intend to move the cursor to click on an element, consult the screenshot to determine its coordinates.\n"
            "* If a click failed to do anything even after waiting, adjust the cursor position so it visually falls on the element.\n"
            "* Click buttons, links and icons with the cursor tip in the center of the element."
        ),
        "parameters": {
            "properties": {
                "action": {
                    "description": (
                        "The action to perform. The available actions are:\n"
                        "* `key`: Performs key down presses on the arguments passed in order, then performs key releases in reverse order.\n"
                        "* `type`: Type a string of text on the keyboard.\n"
                        "* `mouse_move`: Move the cursor to a specified (x, y) pixel coordinate on the screen.\n"
                        "* `left_click`: Click the left mouse button.\n"
                        "* `left_click_drag`: Click and drag the cursor to a specified (x, y) pixel coordinate on the screen.\n"
                        "* `right_click`: Click the right mouse button.\n"
                        "* `middle_click`: Click the middle mouse button.\n"
                        "* `double_click`: Double-click the left mouse button.\n"
                        "* `scroll`: Performs a scroll of the mouse scroll wheel.\n"
                        "* `wait`: Wait specified seconds for the change to happen.\n"
                        "* `terminate`: Terminate the current task and report its completion status."
                    ),
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
                    "description": (
                        "(x, y): The x (pixels from the left edge) and y (pixels from the top edge) "
                        "coordinates to move the mouse to."
                    ),
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
    },
}

GROUNDER_SYSTEM_PROMPT = """You are a helpful assistant.

# Tools

You may call one or more functions to assist with the user query.

You are provided with function signatures within <tools></tools> XML tags:
<tools>
{tools_xml}
</tools>

For each function call, return a json object with function name and arguments within <tool_call></tool_call> XML tags:
<tool_call>
{{"name": <function-name>, "arguments": <args-json-object>}}
</tool_call>"""

PLANNER_SYSTEM_PROMPT = """
You are an agent which follows my instruction and performs web browser tasks as instructed.
You are operating a web application inside a browser viewport of {width}x{height} pixels.
For each step you will get an observation of an image, which is a screenshot of the browser viewport, and you will predict the next action based on the image.
The following rules are IMPORTANT:
- If previous actions didn't achieve the expected result, do not repeat them, especially the last one. Try to adjust either the target or the action based on the new screenshot.
- Do not predict multiple clicks at once. Base each action on the current screenshot; do not predict actions for elements or events not yet visible in the screenshot.
- You cannot complete the task by outputting text content in your response. You must use mouse and keyboard to interact with the page.
- There is no desktop, terminal, or file manager: everything you need is inside the page. Scroll when the element you need is not visible.

You should provide a detailed observation of the current page state based on the full screenshot in the "Observation:" section.
Provide any information that is possibly relevant to achieving the task goal and any elements that may affect the task execution, such as popups, notifications, error messages, loading states.
You MUST return the observation before the thought.

You should think step by step and provide a detailed thought process before generating the next action in the "Thought:" section:
- Step by Step Progress Assessment: what is already done, what went wrong, how to recover
- Next Action Analysis: possible next actions, the most logical one, and its expected consequence
You MUST return the thought before the code.

You are required to use `pyautogui` to perform the action grounded to the observation, but DO NOT use `pyautogui.locateCenterOnScreen` since we have no image of the element, and DO NOT use `pyautogui.screenshot()`.
Return exactly ONE line of python code to perform the action each time. At each step you MUST generate the corresponding instruction to the code before a # in a comment, for example:
```python
# Click the "Add to cart" button in the product card
pyautogui.click(x=0, y=0)
```
The coordinates in the code are placeholders — a separate grounding model resolves them from your comment, so describe the element in detail: what it looks like, where it is, and what happens when you interact with it.
Remember you should only return ONE line of code. You should return the code inside a code block.

Specially, it is also allowed to return the following special code:
When you think you have to wait for some time, return ```WAIT```;
When you think the task can not be done, return ```FAIL```, don't easily say ```FAIL```, try your best to do the task;
When you think the task is done, return ```DONE```.

For your reference, you have a maximum of {max_steps} steps, and the current step is {current_step}.
If you are on the last step, you should return ```DONE``` or ```FAIL``` according to the result.

First give the current screenshot and previous things we did a short reflection, then RETURN ME THE CODE OR SPECIAL CODE I ASKED FOR, NEVER EVER RETURN ME ANYTHING ELSE.
"""

PLANNER_TASK_TEMPLATE = "# Task Instruction:\n{instruction}\n"


def build_grounder_system_prompt(*, width: int, height: int) -> str:
    tools = json.loads(
        json.dumps(GROUNDER_TOOLS).replace("{width}", str(width)).replace("{height}", str(height))
    )
    return GROUNDER_SYSTEM_PROMPT.format(tools_xml=json.dumps(tools))


def build_planner_system_prompt(
    *,
    width: int,
    height: int,
    current_step: int,
    max_steps: int,
) -> str:
    return PLANNER_SYSTEM_PROMPT.format(
        width=width,
        height=height,
        current_step=current_step,
        max_steps=max_steps,
    ).strip()
