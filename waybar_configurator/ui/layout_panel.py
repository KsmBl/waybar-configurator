"""Layout tab: edit a bar's position, monitor, size, margins and behaviour."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from waybar_configurator.ui import widgets


class LayoutPanel(Gtk.Box):
    def __init__(self, bar, on_changed):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_border_width(14)
        self.bar = bar
        self._on_changed = on_changed
        self._build()

    def _changed(self):
        if self._on_changed:
            self._on_changed()

    def _spin(self, value, lower=0, upper=4000):
        adj = Gtk.Adjustment(value=value, lower=lower, upper=upper, step_increment=1)
        s = Gtk.SpinButton(adjustment=adj, digits=0)
        s.set_halign(Gtk.Align.START)
        s.set_size_request(110, -1)
        return s

    def _combo(self, choices, active):
        c = Gtk.ComboBoxText()
        for ch in choices:
            c.append(ch, ch)
        c.set_active_id(active)
        c.set_halign(Gtk.Align.START)
        return c

    def _build(self):
        # ── Placement ─────────────────────────────────────────────────────────
        frame, box = widgets.section_frame("Placement")
        name = Gtk.Entry(text=self.bar.name)
        name.connect("changed", self._set_name)
        box.pack_start(widgets.labelled_row("Bar name", name,
                       "Identifies this bar; also written as Waybar's \"name\" when you have multiple bars."), False, False, 0)

        pos = self._combo(["top", "bottom", "left", "right"], self.bar.position)
        pos.connect("changed", lambda w: (setattr(self.bar, "position", w.get_active_id()), self._changed()))
        box.pack_start(widgets.labelled_row("Position", pos, "Screen edge the bar attaches to."), False, False, 0)

        output = Gtk.Entry(text=self.bar.output)
        output.set_placeholder_text("all monitors")
        output.connect("changed", lambda w: (setattr(self.bar, "output", w.get_text()), self._changed()))
        box.pack_start(widgets.labelled_row("Monitor (output)", output,
                       "e.g. DP-1 / eDP-1. Leave blank for every monitor. Use a different output to place bars side by side."), False, False, 0)

        layer = self._combo(["top", "bottom", "overlay"], self.bar.layer)
        layer.connect("changed", lambda w: (setattr(self.bar, "layer", w.get_active_id()), self._changed()))
        box.pack_start(widgets.labelled_row("Layer", layer, "Stacking layer relative to windows."), False, False, 0)
        self.pack_start(frame, False, False, 0)

        # ── Size ──────────────────────────────────────────────────────────────
        frame, box = widgets.section_frame("Size")
        height = self._spin(self.bar.height)
        height.connect("value-changed", lambda w: (setattr(self.bar, "height", int(w.get_value())), self._changed()))
        box.pack_start(widgets.labelled_row("Height (px, 0 = auto)", height), False, False, 0)
        width = self._spin(self.bar.width)
        width.connect("value-changed", lambda w: (setattr(self.bar, "width", int(w.get_value())), self._changed()))
        box.pack_start(widgets.labelled_row("Width (px, 0 = full)", width,
                       "Set a fixed width plus a margin to place multiple bars next to each other on one edge."), False, False, 0)
        self.pack_start(frame, False, False, 0)

        # ── Margins ───────────────────────────────────────────────────────────
        frame, box = widgets.section_frame("Margins (px)")
        grid = Gtk.Grid(column_spacing=16, row_spacing=8)
        for col, (label, attr) in enumerate([
            ("Top", "margin_top"), ("Right", "margin_right"),
            ("Bottom", "margin_bottom"), ("Left", "margin_left"),
        ]):
            grid.attach(Gtk.Label(label=label, xalign=0.0), col, 0, 1, 1)
            spin = self._spin(getattr(self.bar, attr), lower=0, upper=2000)
            spin.connect("value-changed", lambda w, a=attr: (setattr(self.bar, a, int(w.get_value())), self._changed()))
            grid.attach(spin, col, 1, 1, 1)
        box.pack_start(grid, False, False, 0)
        self.pack_start(frame, False, False, 0)

        # ── Behaviour ─────────────────────────────────────────────────────────
        frame, box = widgets.section_frame("Behaviour")
        spacing = self._spin(self.bar.spacing, lower=0, upper=100)
        spacing.connect("value-changed", lambda w: (setattr(self.bar, "spacing", int(w.get_value())), self._changed()))
        box.pack_start(widgets.labelled_row("Module spacing (px)", spacing), False, False, 0)

        excl = Gtk.Switch(halign=Gtk.Align.START)
        excl.set_active(self.bar.exclusive)
        excl.connect("notify::active", lambda w, _p: (setattr(self.bar, "exclusive", w.get_active()), self._changed()))
        box.pack_start(widgets.labelled_row("Reserve space (exclusive)", excl,
                       "Windows avoid the bar's area when enabled."), False, False, 0)

        pt = Gtk.Switch(halign=Gtk.Align.START)
        pt.set_active(self.bar.passthrough)
        pt.connect("notify::active", lambda w, _p: (setattr(self.bar, "passthrough", w.get_active()), self._changed()))
        box.pack_start(widgets.labelled_row("Click-through (passthrough)", pt,
                       "Mouse events pass through the bar to windows below."), False, False, 0)
        self.pack_start(frame, False, False, 0)

    def _set_name(self, entry):
        self.bar.name = entry.get_text()
        self._changed()
