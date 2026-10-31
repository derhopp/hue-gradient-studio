"""Hue-specific 3-color gradient packet for Zigbee manufacturer cluster 0xFC03.

This is intentionally the same encoder as in the user's working Signe PoC.
Not all Hue lights support this manufacturer-specific command.
"""
from __future__ import annotations

import re

COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
DEFAULT_PRESETS = [
    {"name": "Sonnenuntergang", "colors": ["#FF5722", "#FFB347", "#B54CE0"]},
    {"name": "Lagune", "colors": ["#1346C1", "#19B8C4", "#65E8D4"]},
    {"name": "Galaxie", "colors": ["#24115A", "#6633C8", "#F24A9A"]},
    {"name": "Abendruhe", "colors": ["#F7A34B", "#DE6E85", "#623B98"]},
]


def validate_colors(colors: object) -> list[str]:
    """Require exactly three RGB hex strings and return canonical values."""
    if not isinstance(colors, list) or len(colors) != 3:
        raise ValueError("Exactly three #RRGGBB colors are required")
    if not all(isinstance(c, str) and COLOR_RE.fullmatch(c) for c in colors):
        raise ValueError("Colors must use #RRGGBB")
    return [c.upper() for c in colors]


def encode_color(hex_color: str) -> str:
    """Pack RGB→CIE xy into Philips' interleaved 12-bit format."""
    r, g, b = (int(hex_color[i : i + 2], 16) / 255.0 for i in (1, 3, 5))
    x_val = r * 0.664511 + g * 0.154324 + b * 0.162028
    y_val = r * 0.283881 + g * 0.668433 + b * 0.047685
    z_val = r * 0.000088 + g * 0.072310 + b * 0.986039
    total = x_val + y_val + z_val
    x = 0.0 if total == 0 else x_val / total
    y = 0.0 if total == 0 else y_val / total
    # JavaScript Math.round on nonnegative inputs is floor(value + 0.5).
    xx = f"{max(0, min(4095, int(x * 4095 / 0.7347 + 0.5))):03x}"
    yy = f"{max(0, min(4095, int(y * 4095 / 0.8264 + 0.5))):03x}"
    return f"{xx[1]}{xx[2]}{yy[2]}{xx[0]}{yy[0]}{yy[1]}"


def encode_gradient(colors: list[str], reverse: bool = True) -> str:
    """Build 3-color / 3-segment packet previously tested on Hue Signe."""
    normalized = validate_colors(colors)
    ordered = list(reversed(normalized)) if reverse else normalized
    return "500104000d30000000" + "".join(encode_color(c) for c in ordered) + "1800"
