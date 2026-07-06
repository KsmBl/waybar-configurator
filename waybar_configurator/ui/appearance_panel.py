"""Appearance tab: guided colour/shape/font controls that drive the CSS generator.

The controls are grouped into three switchable pages (Theme / Bar & spacing /
Module colours) so no single view becomes an overwhelming wall of options.
"""

from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from waybar_configurator.model.catalog import get_module_def
from waybar_configurator.ui import widgets


class AppearancePanel(Gtk.Box):
    def __init__(self, config, on_changed):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.config = config
        self.theme = config.theme
        self._on_changed = on_changed
        self._spins = {}
        self._build()

    def _changed(self):
        if self._on_changed:
            self._on_changed()

    # ── layout scaffolding ────────────────────────────────────────────────────
    def _build(self):
        stack = Gtk.Stack()
        stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        stack.set_transition_duration(150)

        switcher = Gtk.StackSwitcher()
        switcher.set_stack(stack)
        switcher.set_halign(Gtk.Align.CENTER)
        switcher.set_margin_top(10)
        switcher.set_margin_bottom(6)
        self.pack_start(switcher, False, False, 0)
        self.pack_start(stack, True, True, 0)

        theme_page = self._page_box()
        theme_page.pack_start(self._section_typography(), False, False, 0)
        theme_page.pack_start(self._section_colours(), False, False, 0)
        stack.add_titled(self._page_scroll(theme_page), "theme", "Theme")

        bar_page = self._page_box()
        bar_page.pack_start(self._section_bar_container(), False, False, 0)
        bar_page.pack_start(self._section_shape_spacing(), False, False, 0)
        bar_page.pack_start(self._section_workspaces(), False, False, 0)
        stack.add_titled(self._page_scroll(bar_page), "bar", "Bar & spacing")

        mod_page = self._page_box()
        mod_page.pack_start(self._section_module_colours(), False, False, 0)
        stack.add_titled(self._page_scroll(mod_page), "modules", "Module colours")

    @staticmethod
    def _page_box():
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_border_width(14)
        return box

    @staticmethod
    def _page_scroll(child):
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sw.add(child)
        return sw

    # ── shared control builders ───────────────────────────────────────────────
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

    @staticmethod
    def _hint(text):
        lbl = Gtk.Label(xalign=0.0)
        lbl.set_markup(f"<small><span alpha='70%'>{widgets._escape(text)}</span></small>")
        lbl.set_line_wrap(True)
        lbl.set_margin_bottom(2)
        return lbl

    # ── sections ──────────────────────────────────────────────────────────────
    def _section_typography(self):
        frame, box = widgets.section_frame("Typography")
        font = Gtk.Entry(text=self.theme.font_family)
        font.connect("changed", lambda w: (setattr(self.theme, "font_family", w.get_text()), self._changed()))
        box.pack_start(widgets.labelled_row("Font family", font,
                       "Comma-separated font stack, e.g. \"JetBrainsMono Nerd Font, sans-serif\"."), False, False, 0)
        size = self._spin(self.theme.font_size, 6, 48)
        size.connect("value-changed", lambda w: (setattr(self.theme, "font_size", int(w.get_value())), self._changed()))
        box.pack_start(widgets.labelled_row("Font size (px)", size), False, False, 0)
        return frame

    def _section_colours(self):
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
        return frame

    def _section_bar_container(self):
        frame, box = widgets.section_frame("Bar container")
        box.pack_start(self._hint(
            "Choose whether left / center / right are separate rounded pills or one "
            "continuous bar, and how the bar insets its content."), False, False, 0)
        style = Gtk.ComboBoxText()
        style.append("groups", "Separate groups (pills)")
        style.append("single", "Single bar")
        style.set_active_id(self.theme.bar_style if self.theme.bar_style in ("groups", "single") else "groups")
        style.connect("changed", lambda w: (setattr(self.theme, "bar_style", w.get_active_id() or "groups"),
                                            self._changed()))
        box.pack_start(widgets.labelled_row(
            "Bar style", style,
            "Separate groups: left / center / right are each their own rounded pill. "
            "Single bar: one continuous background across the whole bar."), False, False, 0)

        for label, attr, lo, hi, tip in [
            ("Bar corner radius (px)", "bar_radius", 0, 40,
             "Rounding of the whole bar. Used with the Single bar style."),
            ("Bar padding — vertical (px)", "bar_padding_v", 0, 40,
             "Inset the content from the bar's top/bottom edge. Different from Margins, "
             "which are the gap outside the bar."),
            ("Bar padding — horizontal (px)", "bar_padding_h", 0, 60,
             "Inset the content from the bar's left/right edge."),
        ]:
            spin = self._spin(getattr(self.theme, attr), lo, hi)
            spin.connect("value-changed", lambda w, a=attr: (setattr(self.theme, a, int(w.get_value())),
                                                             self._changed()))
            box.pack_start(widgets.labelled_row(label, spin, tip), False, False, 0)
        return frame

    def _section_shape_spacing(self):
        frame, box = widgets.section_frame("Shape & spacing")
        box.pack_start(self._hint(
            "Pick a Density for a quick thin/roomy bar, or fine-tune the individual "
            "paddings and margins below."), False, False, 0)

        # Density preset — a one-click way to make the bar thinner or roomier.
        self._density = Gtk.ComboBoxText()
        for name in ["Compact", "Comfortable", "Spacious"]:
            self._density.append(name, name)
        self._density.append("custom", "Custom")
        self._density.set_active_id(self.theme.density_name() or "custom")
        self._density.connect("changed", self._on_density_changed)
        box.pack_start(widgets.labelled_row(
            "Density", self._density,
            "Overall bar thickness. Sets vertical padding and margins; "
            "pick Compact for a thin bar."), False, False, 0)

        for label, attr, lo, hi in [
            ("Vertical padding (px)", "padding_v", 0, 40),
            ("Module vertical margin (px)", "module_margin_v", 0, 30),
            ("Group vertical margin (px)", "group_margin_v", 0, 30),
            ("Horizontal padding (px)", "padding_h", 0, 60),
            ("Module margin (px)", "module_margin", 0, 30),
            ("Group edge spacing (px)", "group_margin_h", 0, 80),
            ("Group horizontal padding (px)", "group_padding_h", 0, 40),
            ("Module corner radius (px)", "corner_radius", 0, 40),
            ("Group corner radius (px)", "group_radius", 0, 40),
        ]:
            spin = self._spin(getattr(self.theme, attr), lo, hi)
            spin.connect("value-changed", lambda w, a=attr: self._on_spin(a, int(w.get_value())))
            self._spins[attr] = spin
            box.pack_start(widgets.labelled_row(label, spin), False, False, 0)
        return frame

    def _section_workspaces(self):
        frame, box = widgets.section_frame("Workspaces")
        ws_width = self._spin(self.theme.workspace_min_width, 0, 200)
        ws_width.connect("value-changed",
                         lambda w: (setattr(self.theme, "workspace_min_width", int(w.get_value())),
                                    self._changed()))
        box.pack_start(widgets.labelled_row(
            "Button width (px)", ws_width,
            "Minimum width of each workspace button. 0 = fit the label. "
            "Set a fixed value for evenly-sized, square-ish buttons."), False, False, 0)
        return frame

    def _section_module_colours(self):
        frame, box = widgets.section_frame("Per-module text colour")
        box.pack_start(self._hint(
            "Tick a module to override its text colour. Everything else uses the "
            "Text colour from the Theme page."), False, False, 0)
        used = sorted(self.config.used_module_types())
        if not used:
            box.pack_start(Gtk.Label(
                label="No modules yet — add some in the Modules tab first.",
                xalign=0.0), False, False, 0)
        for base_type in used:
            box.pack_start(self._module_color_row(base_type), False, False, 0)
        return frame

    # ── density wiring ────────────────────────────────────────────────────────
    _DENSITY_ATTRS = ("padding_v", "module_margin_v", "group_margin_v")

    def _on_spin(self, attr, value):
        setattr(self.theme, attr, value)
        # A manual tweak to a density-controlled value flips the preset to Custom.
        if attr in self._DENSITY_ATTRS and self.theme.density_name() is None:
            self._density.handler_block_by_func(self._on_density_changed)
            self._density.set_active_id("custom")
            self._density.handler_unblock_by_func(self._on_density_changed)
        self._changed()

    def _on_density_changed(self, combo):
        name = combo.get_active_id()
        if name == "custom":
            return
        # Set the model first, then mirror it into the spinners. Because all
        # density-controlled values now match the preset, the spinners' own
        # handlers won't flip the combo back to Custom.
        self.theme.apply_density(name)
        for attr in self._DENSITY_ATTRS:
            self._spins[attr].set_value(getattr(self.theme, attr))
        self._changed()

    # ── per-module colour rows ────────────────────────────────────────────────
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
