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
    padding_v: int = 2          # vertical padding inside each module (top/bottom)
    padding_h: int = 12         # horizontal padding inside each module (left/right)
    module_margin: int = 2      # horizontal gap between modules
    module_margin_v: int = 1    # vertical margin around each module
    group_margin_v: int = 3     # vertical margin around each module group
    group_margin_h: int = 0     # outer horizontal margin (spacing to the bar edge)
    group_padding_h: int = 6    # horizontal padding inside each module group

    # Workspaces: minimum width per workspace button (0 = fit content).
    workspace_min_width: int = 0

    # Bar container. "groups" = each of left/center/right is its own rounded pill
    # (the background/border live on the module groups). "single" = one continuous
    # bar background spanning the whole width, with transparent groups.
    bar_style: str = "groups"
    bar_padding_v: int = 0      # padding inside the bar (insets content from edges)
    bar_padding_h: int = 0
    bar_radius: int = 14        # corner radius of the whole bar (single style)

    # Optional per-module text colour overrides: {base_module_type: "#rrggbb"}
    module_colors: dict = field(default_factory=dict)

    # Named spacing presets that drive the vertical "thickness" of the bar. Only
    # the values that affect height are set; colours/radii/font are left alone.
    DENSITY_PRESETS = {
        "Compact": dict(padding_v=1, module_margin_v=0, group_margin_v=1),
        "Comfortable": dict(padding_v=2, module_margin_v=1, group_margin_v=3),
        "Spacious": dict(padding_v=6, module_margin_v=4, group_margin_v=5),
    }

    def apply_density(self, name: str) -> None:
        preset = self.DENSITY_PRESETS.get(name)
        if preset:
            for key, value in preset.items():
                setattr(self, key, value)

    def density_name(self):
        """Return the preset name matching the current spacing, or None (custom)."""
        for name, preset in self.DENSITY_PRESETS.items():
            if all(getattr(self, key) == value for key, value in preset.items()):
                return name
        return None

    def clone(self) -> "Theme":
        t = copy.copy(self)
        t.module_colors = dict(self.module_colors)
        return t
