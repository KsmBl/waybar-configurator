"""Appearance model — guided values the CSS generator turns into a Waybar style.css."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field


@dataclass
class Theme:
    # Typography
    font_family: str = "GoMono Nerd Font, Noto Sans, monospace"
    font_size: int = 13

    # Colours (hex strings). The module-group background also has an opacity.
    background: str = "#0e1120"      # module-group background
    background_opacity: float = 0.92
    foreground: str = "#dde3f5"      # default text
    accent: str = "#5b8fff"          # borders / focus accent
    hover: str = "#ffffff"           # hover tint (applied at low opacity)
    tooltip_background: str = "#0a0c18"
    tooltip_foreground: str = "#dde3f5"

    # Shape / spacing
    corner_radius: int = 12
    group_radius: int = 14
    padding_v: int = 4
    padding_h: int = 14
    module_margin: int = 2

    # Optional per-module text colour overrides: {base_module_type: "#rrggbb"}
    module_colors: dict = field(default_factory=dict)

    def clone(self) -> "Theme":
        t = copy.copy(self)
        t.module_colors = dict(self.module_colors)
        return t
