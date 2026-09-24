"""Coordinate spaces used by GUI models and the scaler back to screen pixels.

Every family predicts points in its own frame: raw pixels of the resized image
(qwen3-vl absolute), a 0..1 box (opencua relative), 0..999 / 0..1000 grids
(qwen3-vl relative, UI-TARS), or the qwen2.5-VL smart-resize grid. The agent
loop only ever deals in screen pixels, so parsers scale once, here.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from bench_eval.agents.core.images import smart_resize


class CoordinateSpace(str, Enum):
    """Frame a model's raw (x, y) output lives in."""

    #: Pixels of the original screenshot (no rescaling needed).
    SCREEN = "screen"
    #: Pixels of the image actually sent to the model (after smart_resize).
    RESIZED = "resized"
    #: Normalized 0..1 floats (OpenCUA default).
    NORM_1 = "relative"
    #: Normalized 0..999 integer grid (Qwen3-VL relative mode).
    NORM_999 = "relative999"
    #: Normalized 0..1000 integer grid (UI-TARS).
    NORM_1000 = "relative1000"
    #: qwen2.5-VL smart_resize grid computed from the *screen* size.
    QWEN25 = "qwen25"


@dataclass(frozen=True)
class CoordinateScaler:
    """Map model coordinates onto screen pixels.

    ``screen`` is the real viewport (what the executor clicks), ``processed`` is
    the size of the image handed to the model.
    """

    space: CoordinateSpace
    screen_width: int
    screen_height: int
    processed_width: Optional[int] = None
    processed_height: Optional[int] = None
    smart_resize_factor: int = 28

    def to_screen(self, x: float, y: float) -> tuple[int, int]:
        sx, sy = self._scale(float(x), float(y))
        # Clamp: a click one pixel outside the viewport is a hard Playwright error,
        # while the model almost certainly meant the edge element.
        sx = min(max(sx, 0), self.screen_width - 1)
        sy = min(max(sy, 0), self.screen_height - 1)
        return int(round(sx)), int(round(sy))

    def _scale(self, x: float, y: float) -> tuple[float, float]:
        if self.space is CoordinateSpace.SCREEN:
            return x, y

        if self.space is CoordinateSpace.RESIZED:
            if not (self.processed_width and self.processed_height):
                return x, y
            return (
                x * self.screen_width / self.processed_width,
                y * self.screen_height / self.processed_height,
            )

        if self.space is CoordinateSpace.NORM_1:
            # Models sometimes emit absolute pixels despite the relative prompt.
            if x > 1.0 or y > 1.0:
                return x, y
            return x * self.screen_width, y * self.screen_height

        if self.space is CoordinateSpace.NORM_999:
            return x * self.screen_width / 999.0, y * self.screen_height / 999.0

        if self.space is CoordinateSpace.NORM_1000:
            return x * self.screen_width / 1000.0, y * self.screen_height / 1000.0

        if self.space is CoordinateSpace.QWEN25:
            grid_h, grid_w = smart_resize(
                height=self.screen_height,
                width=self.screen_width,
                factor=self.smart_resize_factor,
                min_pixels=3136,
                max_pixels=12845056,
            )
            if 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0:
                return x * self.screen_width, y * self.screen_height
            return x / grid_w * self.screen_width, y / grid_h * self.screen_height

        raise ValueError(f"Unsupported coordinate space: {self.space}")

    def with_processed(self, width: int, height: int) -> "CoordinateScaler":
        return CoordinateScaler(
            space=self.space,
            screen_width=self.screen_width,
            screen_height=self.screen_height,
            processed_width=width,
            processed_height=height,
            smart_resize_factor=self.smart_resize_factor,
        )
