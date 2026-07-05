"""Appearance tab: guided colour/shape/font controls that drive the CSS generator."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from waybar_configurator.model.catalog import get_module_def
from waybar_configurator.ui import widgets


class AppearancePanel(Gtk.Box):
    def __init__(self, config, on_changed):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(14)
        self.config = config
        self.theme = config.theme
        self._on_changed = on_changed
        self._build()

    def _changed(self):
        if self._on_changed:
            self._on_changed()

    def _spin(self, value, lower, upper, step=1, digits=0):
        adj = Gtk.Adjustment(value=value, lower=lower, upper=upper, step_increment=step)
        s = Gtk.SpinButton(adjustment=adj, digits=digits)
        s.set_halign(Gtk.Align.START)
        s.set_size_request(110, -1)
        return s

    def _color_row(self, label, attr, tooltip=""):
        btn = widgets.color_button(
            getattr(self.theme, attr),
            lambda hexv, a=attr: (setattr(self.theme, a, hexv), self._changed()),
        )
        btn.set_halign(Gtk.Align.START)
        return widgets.labelled_row(label, btn, tooltip)

    def _build(self):
        # ── Typography ────────────────────────────────────────────────────────
        frame, box = widgets.section_frame("Typography")
        font = Gtk.Entry(text=self.theme.font_family)
        font.connect("changed", lambda w: (setattr(self.theme, "font_family", w.get_text()), self._changed()))
        box.pack_start(widgets.labelled_row("Font family", font,
                       "Comma-separated font stack, e.g. \"JetBrainsMono Nerd Font, sans-serif\"."), False, False, 0)
        size = self._spin(self.theme.font_size, 6, 48)
        size.connect("value-changed", lambda w: (setattr(self.theme, "font_size", int(w.get_value())), self._changed()))
        box.pack_start(widgets.labelled_row("Font size (px)", size), False, False, 0)
        self.pack_start(frame, False, False, 0)

        # ── Colours ───────────────────────────────────────────────────────────
        frame, box = widgets.section_frame("Colours")
        box.pack_start(self._color_row("Background", "background",
                       "Module-group background colour."), False, False, 0)

        opacity = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.0, 1.0, 0.01)
        opacity.set_value(self.theme.background_opacity)
        opacity.set_digits(2)
        opacity.set_hexpand(True)
        opacity.connect("value-changed", lambda w: (setattr(self.theme, "background_opacity", w.get_value()), self._changed()))
        box.pack_start(widgets.labelled_row("Background opacity", opacity), False, False, 0)

        box.pack_start(self._color_row("Text", "foreground"), False, False, 0)
        box.pack_start(self._color_row("Accent", "accent",
                       "Borders and focus highlights."), False, False, 0)
        box.pack_start(self._color_row("Hover tint", "hover"), False, False, 0)
        box.pack_start(self._color_row("Tooltip background", "tooltip_background"), False, False, 0)
        box.pack_start(self._color_row("Tooltip text", "tooltip_foreground"), False, False, 0)
        self.pack_start(frame, False, False, 0)

        # ── Shape & spacing ───────────────────────────────────────────────────
        frame, box = widgets.section_frame("Shape & spacing")
        for label, attr, lo, hi in [
            ("Module corner radius (px)", "corner_radius", 0, 40),
            ("Group corner radius (px)", "group_radius", 0, 40),
            ("Vertical padding (px)", "padding_v", 0, 40),
            ("Horizontal padding (px)", "padding_h", 0, 60),
            ("Module margin (px)", "module_margin", 0, 30),
        ]:
            spin = self._spin(getattr(self.theme, attr), lo, hi)
            spin.connect("value-changed", lambda w, a=attr: (setattr(self.theme, a, int(w.get_value())), self._changed()))
            box.pack_start(widgets.labelled_row(label, spin), False, False, 0)
        self.pack_start(frame, False, False, 0)

        # ── Per-module colours ────────────────────────────────────────────────
        frame, box = widgets.section_frame("Per-module text colour")
        box.pack_start(Gtk.Label(
            label="Enable to override the text colour of an individual module.",
            xalign=0.0), False, False, 0)
        used = sorted(self.config.used_module_types())
        if not used:
            box.pack_start(Gtk.Label(label="Add modules first.", xalign=0.0), False, False, 0)
        for base_type in used:
            box.pack_start(self._module_color_row(base_type), False, False, 0)
        self.pack_start(frame, False, False, 0)

    def _module_color_row(self, base_type):
        md = get_module_def(base_type)
        name = md.name if md else base_type
        enabled = base_type in self.theme.module_colors

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        check = Gtk.CheckButton()
        check.set_active(enabled)
        lbl = Gtk.Label(label=name, xalign=0.0)
        lbl.set_size_request(180, -1)
        btn = widgets.color_button(self.theme.module_colors.get(base_type, self.theme.foreground),
                                   lambda hexv, bt=base_type, c=check: self._set_module_color(bt, hexv, c))
        btn.set_halign(Gtk.Align.START)
        btn.set_sensitive(enabled)

        def _on_toggle(c, bt=base_type, button=btn):
            if c.get_active():
                self.theme.module_colors[bt] = widgets.rgba_to_hex(button.get_rgba())
                button.set_sensitive(True)
            else:
                self.theme.module_colors.pop(bt, None)
                button.set_sensitive(False)
            self._changed()

        check.connect("toggled", _on_toggle)
        row.pack_start(check, False, False, 0)
        row.pack_start(lbl, False, False, 0)
        row.pack_start(btn, False, False, 0)
        return row

    def _set_module_color(self, base_type, hexv, check):
        self.theme.module_colors[base_type] = hexv
        if not check.get_active():
            check.set_active(True)
        self._changed()
