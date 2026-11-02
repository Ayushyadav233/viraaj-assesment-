import logging
import math
from pathlib import Path
from typing import Optional, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# System TrueType Fonts with universal fallback
WINDOWS_FONTS = [
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/arial.ttf",
]
WINDOWS_REGULAR_FONTS = [
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
]


def _get_font(size: int, bold: bool = True) -> ImageFont.ImageFont:
    """Returns a high-legibility TrueType font with universal fallback."""
    font_candidates = WINDOWS_FONTS if bold else WINDOWS_REGULAR_FONTS
    for font_path in font_candidates:
        if Path(font_path).exists():
            try:
                return ImageFont.truetype(font_path, size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap_text(text: str, font: ImageFont.ImageFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """Wraps text to comfortably fit within max_width pixels."""
    words = text.split()
    if not words:
        return []
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(word)
    if current_line:
        lines.append(" ".join(current_line))
    return lines


def create_placeholder_background(width: int, height: int, title: str) -> Image.Image:
    """Generates an ultra-luxury dark architectural gradient background when an image is missing."""
    base = Image.new("RGB", (width, height))
    draw = ImageDraw.Draw(base)

    top_color = (15, 23, 42)    # Deep Slate
    bottom_color = (2, 6, 23)   # Rich Obsidian

    for y in range(height):
        ratio = y / height
        r = int(top_color[0] * (1 - ratio) + bottom_color[0] * ratio)
        g = int(top_color[1] * (1 - ratio) + bottom_color[1] * ratio)
        b = int(top_color[2] * (1 - ratio) + bottom_color[2] * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Elegant subtle architectural grid
    for x in range(0, width, 140):
        draw.line([(x, 0), (x, height)], fill=(30, 41, 59), width=1)
    for y in range(0, height, 140):
        draw.line([(0, y), (width, y)], fill=(30, 41, 59), width=1)

    return base


def load_and_prep_image(
    image_path: Optional[str],
    target_w: int,
    target_h: int,
    motion_margin: float = 0.16,
) -> Image.Image:
    """Loads, validates, and crops an image with extra buffer space for cinematic camera motion."""
    buffer_w = int(target_w * (1.0 + motion_margin))
    buffer_h = int(target_h * (1.0 + motion_margin))

    if image_path:
        p = Path(image_path)
        if p.exists() and p.is_file():
            try:
                with Image.open(p) as img:
                    img = img.convert("RGB")
                    orig_w, orig_h = img.size

                    scale = max(buffer_w / orig_w, buffer_h / orig_h)
                    new_w = int(orig_w * scale)
                    new_h = int(orig_h * scale)

                    resized = img.resize((new_w, new_h), Image.Resampling.LANCZOS)

                    left = (new_w - buffer_w) // 2
                    top = (new_h - buffer_h) // 2
                    return resized.crop((left, top, left + buffer_w, top + buffer_h))
            except Exception as e:
                logger.warning("Could not read image %s (%s). Using luxury placeholder.", image_path, e)

    return create_placeholder_background(buffer_w, buffer_h, "Luxury Real Estate")


def create_overlay_card(
    target_w: int,
    target_h: int,
    badge_text: str,
    headline: str,
    subtext: str,
    orientation: str = "16:9",
    watermark_text: str = "REALTY ASSISTANT EXCLUSIVE",
) -> Image.Image:
    """Pre-renders an ultra-luxury commercial broadcast lower-third card with watermark."""
    overlay = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    is_vertical = orientation == "9:16"
    is_square = orientation == "1:1"

    # 1. Top-Left Luxury Brand Watermark
    if watermark_text and watermark_text.strip():
        font_brand = _get_font(18 if orientation == "16:9" else 15, bold=True)
        bbox_brand = draw.textbbox((0, 0), watermark_text, font=font_brand)
        bw_brand = bbox_brand[2] - bbox_brand[0]
        draw.rounded_rectangle(
            [(32, 28), (32 + bw_brand + 28, 64)],
            radius=6,
            fill=(15, 23, 42, 205),
            outline=(217, 119, 6, 190),
            width=1,
        )
        draw.text((46, 36), watermark_text, font=font_brand, fill=(245, 158, 11, 245))

    # 2. Lower-Third Container Sizing & Positioning
    if is_vertical:
        card_w = int(target_w * 0.92)
        card_x0 = (target_w - card_w) // 2
        card_y1 = int(target_h * 0.86)
        max_card_h = int(target_h * 0.32)
        headline_size = 44
        subtext_size = 26
        badge_size = 20
    elif is_square:
        card_w = int(target_w * 0.90)
        card_x0 = (target_w - card_w) // 2
        card_y1 = int(target_h * 0.88)
        max_card_h = int(target_h * 0.35)
        headline_size = 40
        subtext_size = 24
        badge_size = 18
    else:  # 16:9
        card_w = int(target_w * 0.78)
        card_x0 = 48
        card_y1 = int(target_h * 0.90)
        max_card_h = int(target_h * 0.32)
        headline_size = 46
        subtext_size = 26
        badge_size = 20

    font_badge = _get_font(badge_size, bold=True)
    font_headline = _get_font(headline_size, bold=True)
    font_subtext = _get_font(subtext_size, bold=False)

    text_inner_w = card_w - 75
    headline_lines = _wrap_text(headline, font_headline, text_inner_w, draw)[:2]
    subtext_lines = _wrap_text(subtext, font_subtext, text_inner_w, draw)[:3]

    line_h_head = headline_size + 8
    line_h_sub = subtext_size + 7
    content_h = (
        24 + badge_size + 14
        + len(headline_lines) * line_h_head + 12
        + len(subtext_lines) * line_h_sub + 24
    )
    card_h = max(150, min(content_h, max_card_h))
    card_y0 = card_y1 - card_h
    card_x1 = card_x0 + card_w

    # Frosted glass dark background with subtle border
    card_bg_color = (15, 23, 42, 225)
    border_color = (51, 65, 85, 200)

    draw.rounded_rectangle(
        [(card_x0, card_y0), (card_x1, card_y1)],
        radius=14,
        fill=card_bg_color,
        outline=border_color,
        width=1,
    )

    # 4px Golden accent vertical bar on the left edge
    draw.rounded_rectangle(
        [(card_x0 + 4, card_y0 + 10), (card_x0 + 9, card_y1 - 10)],
        radius=3,
        fill=(217, 119, 6, 255),
    )

    # Category Badge (Gold pill)
    curr_y = card_y0 + 20
    badge_str = f" {badge_text.upper()} "
    bbox_badge = draw.textbbox((0, 0), badge_str, font=font_badge)
    bw = bbox_badge[2] - bbox_badge[0]
    bh = bbox_badge[3] - bbox_badge[1]

    draw.rounded_rectangle(
        [(card_x0 + 28, curr_y - 2), (card_x0 + 28 + bw + 14, curr_y + bh + 4)],
        radius=6,
        fill=(217, 119, 6, 230),
    )
    draw.text((card_x0 + 35, curr_y + 1), badge_str, font=font_badge, fill=(255, 255, 255, 255))

    curr_y += bh + 16

    # Bold Headline with subtle drop shadow
    for line in headline_lines:
        draw.text((card_x0 + 30, curr_y + 2), line, font=font_headline, fill=(0, 0, 0, 220))
        draw.text((card_x0 + 28, curr_y), line, font=font_headline, fill=(255, 255, 255, 255))
        curr_y += line_h_head

    curr_y += 4

    # Subtext (Silver / Light Platinum)
    for line in subtext_lines:
        draw.text((card_x0 + 28, curr_y), line, font=font_subtext, fill=(226, 232, 240, 240))
        curr_y += line_h_sub

    return overlay


def build_scene_frame_generator(
    image_path: Optional[str],
    badge_text: str,
    headline: str,
    subtext: str,
    duration: float,
    orientation: str = "16:9",
    motion_type: str = "zoom_in",
    watermark_text: str = "REALTY ASSISTANT EXCLUSIVE",
    show_progress_bar: bool = True,
):
    """Returns a callable make_frame(t) for MoviePy with dynamic cinematic camera motions."""
    if orientation == "9:16":
        target_w, target_h = (1080, 1920)
    elif orientation == "1:1":
        target_w, target_h = (1080, 1080)
    else:
        target_w, target_h = (1920, 1080)

    motion_margin = 0.16
    buffer_img = load_and_prep_image(image_path, target_w, target_h, motion_margin=motion_margin)
    buffer_w, buffer_h = buffer_img.size

    # Pre-render static card overlay once
    overlay_card = create_overlay_card(
        target_w=target_w,
        target_h=target_h,
        badge_text=badge_text,
        headline=headline,
        subtext=subtext,
        orientation=orientation,
        watermark_text=watermark_text,
    )

    def make_frame(t: float) -> np.ndarray:
        progress = min(1.0, max(0.0, t / max(duration, 0.1)))

        # 1. Compute dynamic camera motion based on motion_type
        if motion_type == "zoom_in":
            scale = 1.0 + (motion_margin * progress)
            curr_w = int(target_w * scale)
            curr_h = int(target_h * scale)
            left = max(0, (buffer_w - curr_w) // 2)
            top = max(0, (buffer_h - curr_h) // 2)

        elif motion_type == "zoom_out":
            scale = (1.0 + motion_margin) - (motion_margin * progress)
            curr_w = int(target_w * scale)
            curr_h = int(target_h * scale)
            left = max(0, (buffer_w - curr_w) // 2)
            top = max(0, (buffer_h - curr_h) // 2)

        elif motion_type == "pan_right":
            scale = 1.0 + (motion_margin * 0.5)
            curr_w = int(target_w * scale)
            curr_h = int(target_h * scale)
            extra_x = buffer_w - curr_w
            left = int(extra_x * progress)
            top = max(0, (buffer_h - curr_h) // 2)

        elif motion_type == "pan_left":
            scale = 1.0 + (motion_margin * 0.5)
            curr_w = int(target_w * scale)
            curr_h = int(target_h * scale)
            extra_x = buffer_w - curr_w
            left = int(extra_x * (1.0 - progress))
            top = max(0, (buffer_h - curr_h) // 2)

        else:  # drift_up
            scale = 1.0 + (motion_margin * 0.5 * progress)
            curr_w = int(target_w * scale)
            curr_h = int(target_h * scale)
            extra_y = buffer_h - curr_h
            left = max(0, (buffer_w - curr_w) // 2)
            top = int(extra_y * (1.0 - progress))

        crop_box = (
            min(max(0, left), buffer_w - 10),
            min(max(0, top), buffer_h - 10),
            min(buffer_w, left + curr_w),
            min(buffer_h, top + curr_h),
        )

        cropped = buffer_img.crop(crop_box)
        resized_frame = cropped.resize((target_w, target_h), Image.Resampling.BILINEAR)

        # Composite pre-rendered text overlay card
        resized_frame.paste(overlay_card, (0, 0), overlay_card)

        # Dynamic Golden Progress Bar along the bottom edge
        if show_progress_bar:
            draw = ImageDraw.Draw(resized_frame)
            bar_w = int(target_w * progress)
            if bar_w > 0:
                draw.rectangle([(0, target_h - 6), (bar_w, target_h)], fill=(217, 119, 6))

        return np.array(resized_frame)

    return make_frame, target_w, target_h
