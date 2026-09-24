"""Screenshot preprocessing shared by the GUI model families.

``smart_resize`` mirrors the qwen-vl-utils implementation used to train all five
families, so the pixel grid a model predicts on matches what it saw in training.
"""

from __future__ import annotations

import base64
import math
from dataclasses import dataclass
from io import BytesIO


def round_by_factor(number: float, factor: int) -> int:
    return round(number / factor) * factor


def ceil_by_factor(number: float, factor: int) -> int:
    return math.ceil(number / factor) * factor


def floor_by_factor(number: float, factor: int) -> int:
    return math.floor(number / factor) * factor


def smart_resize(
    height: int,
    width: int,
    factor: int = 28,
    min_pixels: int = 56 * 56,
    max_pixels: int = 14 * 14 * 4 * 1280,
    max_long_side: int = 8192,
) -> tuple[int, int]:
    """Return (height, width) divisible by ``factor`` within the pixel budget."""
    if height < 2 or width < 2:
        raise ValueError(f"height={height} and width={width} must exceed 2")
    if max(height, width) / min(height, width) > 200:
        raise ValueError(f"aspect ratio must stay below 200, got {height}/{width}")

    if max(height, width) > max_long_side:
        beta = max(height, width) / max_long_side
        height, width = int(height / beta), int(width / beta)

    h_bar = round_by_factor(height, factor)
    w_bar = round_by_factor(width, factor)
    if h_bar * w_bar > max_pixels:
        beta = math.sqrt((height * width) / max_pixels)
        h_bar = floor_by_factor(height / beta, factor)
        w_bar = floor_by_factor(width / beta, factor)
    elif h_bar * w_bar < min_pixels:
        beta = math.sqrt(min_pixels / (height * width))
        h_bar = ceil_by_factor(height * beta, factor)
        w_bar = ceil_by_factor(width * beta, factor)
    return h_bar, w_bar


@dataclass(frozen=True)
class ProcessedImage:
    """A screenshot resized for one model family."""

    base64_png: str
    width: int
    height: int
    original_width: int
    original_height: int

    @property
    def data_url(self) -> str:
        return f"data:image/png;base64,{self.base64_png}"


def encode_image(image_bytes: bytes) -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def image_size(image_bytes: bytes) -> tuple[int, int]:
    from PIL import Image

    with Image.open(BytesIO(image_bytes)) as image:
        return image.size


def process_screenshot(
    image_bytes: bytes,
    *,
    factor: int = 28,
    min_pixels: int = 56 * 56,
    max_pixels: int = 14 * 14 * 4 * 1280,
    resize: bool = True,
) -> ProcessedImage:
    """Resize a PNG screenshot onto the model's patch grid."""
    from PIL import Image

    with Image.open(BytesIO(image_bytes)) as image:
        image = image.convert("RGB")
        original_width, original_height = image.size

        if not resize:
            return ProcessedImage(
                base64_png=encode_image(image_bytes),
                width=original_width,
                height=original_height,
                original_width=original_width,
                original_height=original_height,
            )

        resized_height, resized_width = smart_resize(
            height=original_height,
            width=original_width,
            factor=factor,
            min_pixels=min_pixels,
            max_pixels=max_pixels,
        )
        resized = image.resize((resized_width, resized_height))
        buffer = BytesIO()
        resized.save(buffer, format="PNG")

    return ProcessedImage(
        base64_png=encode_image(buffer.getvalue()),
        width=resized_width,
        height=resized_height,
        original_width=original_width,
        original_height=original_height,
    )
