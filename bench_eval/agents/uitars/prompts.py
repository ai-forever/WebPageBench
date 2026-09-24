"""UI-TARS prompts: a compact DSL action space with an explicit Thought section."""

from __future__ import annotations

ACTION_SPACE = """click(start_box='<|box_start|>(x1,y1)<|box_end|>')
left_double(start_box='<|box_start|>(x1,y1)<|box_end|>')
right_single(start_box='<|box_start|>(x1,y1)<|box_end|>')
drag(start_box='<|box_start|>(x1,y1)<|box_end|>', end_box='<|box_start|>(x3,y3)<|box_end|>')
hotkey(key='')
type(content='') #If you want to submit your input, use "\\n" at the end of `content`.
scroll(start_box='<|box_start|>(x1,y1)<|box_end|>', direction='down or up or right or left')
wait() #Sleep for 5s and take a screenshot to check for any changes.
finished(content='xxx') # Use escape characters \\', \\", and \\n in content part to ensure we can parse the content in normal python string format.
"""

ACTION_SPACE_CALL_USER = (
    ACTION_SPACE
    + "call_user() # Submit the task and call the user when the task is unsolvable, "
    "or when you need the user's help.\n"
)

SYSTEM_PROMPT = """You are a GUI agent operating a web browser. You are given a task and your action history, with screenshots. You need to perform the next action to complete the task.

## Output Format
```
Thought: ...
Action: ...
```

## Action Space
{action_space}

## Note
- Use {language} in `Thought` part.
- The screen is a browser viewport showing a web application; scroll when the target element is not visible.
- Write a small plan and finally summarize your next action (with its target element) in one sentence in `Thought` part.

## User Instruction
{instruction}
"""

SYSTEM_PROMPT_NO_THOUGHT = """You are a GUI agent operating a web browser. You are given a task and your action history, with screenshots. You need to perform the next action to complete the task.

## Output Format
```
Action: ...
```

## Action Space
{action_space}

## User Instruction
{instruction}
"""


def build_prompt(
    instruction: str,
    *,
    language: str = "English",
    use_thought: bool = True,
    allow_call_user: bool = False,
) -> str:
    action_space = ACTION_SPACE_CALL_USER if allow_call_user else ACTION_SPACE
    template = SYSTEM_PROMPT if use_thought else SYSTEM_PROMPT_NO_THOUGHT
    return template.format(
        action_space=action_space,
        language=language,
        instruction=instruction,
    )
