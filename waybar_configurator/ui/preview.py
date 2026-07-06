"""A live, in-app mock of the bar being edited.

This is a GTK approximation — not a real Waybar surface — but it reflects the
theme (colours, pill vs. single bar, radii, padding, spacing, fonts) and the
module layout so users get immediate visual feedback while editing.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk  # noqa: E402

from waybar_configurator.io.cssgen import rgba
from waybar_configurator.model.catalog import get_module_def

# Representative sample text so chips look like a real bar rather than raw names.
SAMPLE_TEXT = {
    "clock": "9:41",
    "cpu": "12%",
    "memory": "5.2G",
    "disk": "45%",
    "temperature": "52°",
    "backlight": "60%",
    "pulseaudio": "42%",
    "wireplumber": "42%",
    "battery": "85%",
    "network": "wlan0",
    "bluetooth": "BT",
    "idle_inhibitor": "",
    "tray": "",
    "sway/mode": "default",
    "custom/weather": "21°",
    "custom/disk-io": "R/W",
    "custom/net-bandwidth": "1.2M",
}

_PROVIDER_PRIORITY = Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION + 5


class BarPreview(Gtk.Box):
    def __init__(self, config, bar_index=0):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.config = config
        self.bar_index = bar_index

        self._provider = Gtk.CssProvider()
        screen = Gdk.Screen.get_default()
        if screen is not None:
            Gtk.StyleContext.add_provider_for_screen(screen, self._provider, _PROVIDER_PRIORITY)

        header = Gtk.Label(xalign=0.0)
        header.set_markup("<small><span alpha='70%'>LIVE PREVIEW</span></small>")
        header.set_margin_start(10)
        header.set_margin_top(4)
        self.pack_start(header, False, False, 0)

        self._canvas = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self._canvas.get_style_context().add_class("wbc-preview-canvas")
        self.pack_start(self._canvas, False, False, 0)

        self.refresh()

    # ── public API ────────────────────────────────────────────────────────────
    def set_bar_index(self, index):
        self.bar_index = index
        self.refresh()

    def refresh(self):
        self._provider.load_from_data(self._build_css().encode("utf-8"))
        for child in self._canvas.get_children():
            self._canvas.remove(child)
        bar = self._current_bar()
        if bar is None:
            self._canvas.show_all()
            return
        self._canvas.pack_start(self._build_bar(bar), True, True, 0)
        self._canvas.show_all()

    # ── model access ──────────────────────────────────────────────────────────
    def _current_bar(self):
        bars = self.config.bars
        if not bars:
            return None
        return bars[max(0, min(self.bar_index, len(bars) - 1))]

    # ── widget construction ───────────────────────────────────────────────────
    def _build_bar(self, bar):
        theme = self.config.theme
        single = theme.bar_style == "single"

        bar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        ctx = bar_box.get_style_context()
        ctx.add_class("wbc-preview-bar")
        ctx.add_class("single" if single else "groups")

        left = self._build_group(bar.modules_left, single)
        center = self._build_group(bar.modules_center, single)
        right = self._build_group(bar.modules_right, single)

        bar_box.pack_start(left or Gtk.Box(), False, False, 0)
        bar_box.pack_start(Gtk.Box(), True, True, 0)
        bar_box.pack_start(center or Gtk.Box(), False, False, 0)
        bar_box.pack_start(Gtk.Box(), True, True, 0)
        bar_box.pack_start(right or Gtk.Box(), False, False, 0)
        return bar_box

    def _build_group(self, modules, single):
        if not modules:
            return None
        group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        ctx = group.get_style_context()
        ctx.add_class("wbc-preview-group")
        ctx.add_class("single" if single else "groups")
        for inst in modules:
            group.pack_start(self._build_chip(inst), False, False, 0)
        return group

    def _build_chip(self, inst):
        base = inst.base_type
        if base in ("sway/workspaces", "hyprland/workspaces"):
            return self._build_workspaces(inst)

        icon = inst.icon()
        sample = SAMPLE_TEXT.get(base)
        if sample is None:
            md = get_module_def(base)
            sample = md.name if md else base
        text = f"{icon} {sample}".strip() if icon else sample
        chip = Gtk.Label(label=text)
        chip.get_style_context().add_class("wbc-preview-chip")
        return chip

    def _build_workspaces(self, inst):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        box.get_style_context().add_class("wbc-preview-chip-plain")
        for i, label in enumerate(("1", "2", "3")):
            btn = Gtk.Label(label=label)
            bctx = btn.get_style_context()
            bctx.add_class("wbc-preview-ws")
            if i == 0:
                bctx.add_class("active")
            box.pack_start(btn, False, False, 0)
        return box

    # ── CSS ───────────────────────────────────────────────────────────────────
    def _build_css(self):
        t = self.config.theme
        single = t.bar_style == "single"
        group_bg = rgba(t.background, t.background_opacity)
        group_border = rgba(t.accent, 0.22)

        # The canvas emulates the desktop behind a floating bar.
        canvas_pad = min(max(getattr(self._current_bar(), "margin_top", 8) if self._current_bar() else 8, 6), 28)

        bar_bg = f"background-color: {group_bg};" if single else "background: transparent;"
        bar_radius = f"border-radius: {t.bar_radius}px;" if single and t.bar_radius > 0 else ""
        bar_pad = f"padding: {t.bar_padding_v}px {t.bar_padding_h}px;"

        if single:
            group_style = "background-color: transparent; border: none;"
        else:
            group_style = (f"background-color: {group_bg};"
                           f"border: 1px solid {group_border};"
                           f"border-radius: {t.group_radius}px;")

        ws_width = f"min-width: {t.workspace_min_width}px;" if t.workspace_min_width > 0 else ""

        return f"""
        .wbc-preview-canvas {{
            background-image: linear-gradient(135deg, #3a3f4b, #23262e);
            padding: {canvas_pad}px;
        }}
        .wbc-preview-bar {{
            {bar_bg} {bar_radius} {bar_pad}
            color: {t.foreground};
            font-family: {t.font_family};
            font-size: {t.font_size}px;
        }}
        .wbc-preview-group {{
            {group_style}
            margin: {t.group_margin_v}px {t.group_margin_h}px;
            padding: 0 {t.group_padding_h}px;
        }}
        .wbc-preview-chip {{
            padding: {t.padding_v}px {t.padding_h}px;
            margin: {t.module_margin_v}px {t.module_margin}px;
            border-radius: {t.corner_radius}px;
            color: {t.foreground};
        }}
        .wbc-preview-ws {{
            padding: {t.padding_v}px {max(t.padding_h - 3, 0)}px;
            margin: {t.module_margin_v}px {t.module_margin}px;
            border-radius: {t.corner_radius}px;
            color: {t.foreground};
            {ws_width}
        }}
        .wbc-preview-ws.active {{
            background-color: {rgba(t.accent, 0.18)};
            font-weight: bold;
        }}
        """
