"""Modules tab: three reorderable columns (left/center/right) + a settings form."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from waybar_configurator.model.catalog import CATEGORIES, MODULE_CATALOG
from waybar_configurator.model.config import new_module_instance
from waybar_configurator.ui import widgets
from waybar_configurator.ui.module_form import ModuleForm

PLACEMENT_LABELS = {"left": "Left", "center": "Center", "right": "Right"}


class ColumnView(Gtk.Box):
    """One placement column with its module list and reorder toolbar."""

    def __init__(self, placement, panel):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.placement = placement
        self.panel = panel

        self.header = Gtk.Label(xalign=0.0)
        self.pack_start(self.header, False, False, 0)

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.connect("row-selected", self._on_row_selected)
        self.listbox.set_placeholder(self._empty_placeholder())
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sw.set_min_content_height(170)
        sw.add(self.listbox)
        sw.set_shadow_type(Gtk.ShadowType.IN)
        self.pack_start(sw, True, True, 0)

        # A prominent, full-width add button, with the reorder/remove tools below.
        add_btn = Gtk.Button.new_from_icon_name("list-add-symbolic", Gtk.IconSize.BUTTON)
        add_btn.set_label("Add module")
        add_btn.set_always_show_image(True)
        add_btn.set_tooltip_text(f"Add a module to the {PLACEMENT_LABELS[placement].lower()} section")
        add_btn.connect("clicked", self._on_add)
        self.pack_start(add_btn, False, False, 0)

        tools = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        up = Gtk.Button.new_from_icon_name("go-up-symbolic", Gtk.IconSize.BUTTON)
        up.set_tooltip_text("Move selected module up")
        up.connect("clicked", lambda _b: self._move(-1))
        down = Gtk.Button.new_from_icon_name("go-down-symbolic", Gtk.IconSize.BUTTON)
        down.set_tooltip_text("Move selected module down")
        down.connect("clicked", lambda _b: self._move(1))
        rm = Gtk.Button.new_from_icon_name("edit-delete-symbolic", Gtk.IconSize.BUTTON)
        rm.set_tooltip_text("Remove selected module")
        rm.connect("clicked", lambda _b: self._remove())
        tools.pack_start(up, True, True, 0)
        tools.pack_start(down, True, True, 0)
        tools.pack_start(rm, True, True, 0)
        self.pack_start(tools, False, False, 0)

    # ── model helpers ─────────────────────────────────────────────────────────
    @property
    def modules(self):
        return self.panel.bar.modules_for(self.placement)

    @staticmethod
    def _empty_placeholder():
        lbl = Gtk.Label(xalign=0.5)
        lbl.set_markup("<span alpha='55%'>Empty\nClick “Add module”</span>")
        lbl.set_justify(Gtk.Justification.CENTER)
        lbl.set_margin_top(24)
        lbl.set_margin_bottom(24)
        lbl.show()
        return lbl

    def _update_header(self):
        n = len(self.modules)
        count = f"  <span alpha='55%'>({n})</span>" if n else ""
        self.header.set_markup(f"<b>{PLACEMENT_LABELS[self.placement]}</b>{count}")

    def refresh(self, select_index=None):
        for child in self.listbox.get_children():
            self.listbox.remove(child)
        for inst in self.modules:
            self.listbox.add(self._make_row(inst))
        self.listbox.show_all()
        self._update_header()
        if select_index is not None and 0 <= select_index < len(self.modules):
            row = self.listbox.get_row_at_index(select_index)
            self.listbox.select_row(row)

    def _make_row(self, inst):
        row = Gtk.ListBoxRow()
        row._instance = inst
        hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        hb.set_border_width(6)
        hb.pack_start(Gtk.Label(label=inst.icon()), False, False, 0)
        hb.pack_start(Gtk.Label(label=inst.display_name(), xalign=0.0), True, True, 0)
        row.add(hb)
        return row

    def selected_index(self):
        row = self.listbox.get_selected_row()
        return row.get_index() if row else -1

    # ── events ────────────────────────────────────────────────────────────────
    def _on_row_selected(self, _listbox, row):
        if row is not None:
            self.panel.on_module_selected(self, row._instance)

    def _on_add(self, button):
        self.panel.show_add_popover(button, self.placement)

    def _move(self, delta):
        idx = self.selected_index()
        if idx < 0:
            return
        new = idx + delta
        if not (0 <= new < len(self.modules)):
            return
        self.modules[idx], self.modules[new] = self.modules[new], self.modules[idx]
        self.refresh(select_index=new)
        self.panel.mark_changed()

    def _remove(self):
        idx = self.selected_index()
        if idx < 0:
            return
        self.modules.pop(idx)
        self.refresh()
        self.panel._show_placeholder()
        self.panel.mark_changed()


class ModulesPanel(Gtk.Box):
    def __init__(self, bar, on_changed):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_border_width(12)
        self.bar = bar
        self._on_changed = on_changed

        intro = Gtk.Label(xalign=0.0)
        intro.set_markup(
            "<small><span alpha='70%'>Modules appear on the bar left to right within "
            "each section. Add modules to Left, Center or Right, reorder them, then select "
            "one to edit its settings.</span></small>")
        intro.set_line_wrap(True)
        self.pack_start(intro, False, False, 0)

        columns_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12,
                              homogeneous=True)
        self.columns = {}
        for placement in ("left", "center", "right"):
            col = ColumnView(placement, self)
            self.columns[placement] = col
            columns_box.pack_start(col, True, True, 0)
        self.pack_start(columns_box, False, False, 0)

        settings_frame, settings_box = widgets.section_frame("Module settings")
        self._settings_container = settings_box
        settings_sw = Gtk.ScrolledWindow()
        settings_sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        settings_sw.add(settings_frame)
        self.pack_start(settings_sw, True, True, 0)

        self.refresh_all()
        self._show_placeholder()

    def _show_placeholder(self):
        self.clear_settings()
        placeholder = Gtk.Label(xalign=0.5)
        placeholder.set_markup(
            "<span alpha='60%'>Select a module above to edit its settings.</span>")
        placeholder.set_margin_top(18)
        placeholder.set_margin_bottom(18)
        self._settings_container.pack_start(placeholder, True, True, 0)
        self._settings_container.show_all()

    def refresh_all(self):
        for col in self.columns.values():
            col.refresh()

    def mark_changed(self):
        if self._on_changed:
            self._on_changed()

    def clear_settings(self):
        for child in self._settings_container.get_children():
            self._settings_container.remove(child)

    def on_module_selected(self, column, instance):
        for placement, col in self.columns.items():
            if col is not column:
                col.listbox.unselect_all()
        self.clear_settings()
        form = ModuleForm(instance, self._on_form_changed)
        self._settings_container.pack_start(form, True, True, 0)
        self._settings_container.show_all()

    def _on_form_changed(self):
        # A field changed; the display name may have changed too (rare). Just mark dirty.
        self.mark_changed()

    # ── add-module popover ────────────────────────────────────────────────────
    def show_add_popover(self, relative_to, placement):
        pop = Gtk.Popover.new(relative_to)
        pop.set_position(Gtk.PositionType.BOTTOM)
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        outer.set_border_width(8)
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sw.set_min_content_height(360)
        sw.set_min_content_width(260)
        inner = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)

        for category in CATEGORIES:
            mods = [m for m in MODULE_CATALOG if m.category == category]
            if not mods:
                continue
            cat = Gtk.Label(xalign=0.0)
            cat.set_markup(f"<b>{widgets._escape(category)}</b>")
            cat.set_margin_top(6)
            inner.pack_start(cat, False, False, 0)
            for md in mods:
                btn = Gtk.Button()
                btn.set_relief(Gtk.ReliefStyle.NONE)
                hb = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                hb.pack_start(Gtk.Label(label=md.icon), False, False, 0)
                lbl = Gtk.Label(label=md.name, xalign=0.0)
                hb.pack_start(lbl, True, True, 0)
                btn.add(hb)
                btn.connect("clicked", self._on_pick_module, md, placement, pop)
                inner.pack_start(btn, False, False, 0)

        sw.add(inner)
        outer.pack_start(sw, True, True, 0)
        pop.add(outer)
        pop.show_all()
        pop.popup()

    def _on_pick_module(self, _btn, md, placement, popover):
        popover.popdown()
        module_type = md.key
        if md.needs_instance_name:
            name = self._prompt_instance_name(md)
            if not name:
                return
            module_type = f"custom/{name}"
        inst = new_module_instance(module_type)
        self.bar.modules_for(placement).append(inst)
        col = self.columns[placement]
        col.refresh(select_index=len(self.bar.modules_for(placement)) - 1)
        self.mark_changed()

    def _prompt_instance_name(self, md):
        dialog = Gtk.Dialog(title="Custom module name", modal=True,
                            transient_for=self.get_toplevel())
        dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Add", Gtk.ResponseType.OK)
        box = dialog.get_content_area()
        box.set_border_width(12)
        box.set_spacing(8)
        box.pack_start(Gtk.Label(label="Name for this custom module (e.g. mymodule):",
                                xalign=0.0), False, False, 0)
        entry = Gtk.Entry()
        entry.set_placeholder_text("mymodule")
        entry.connect("activate", lambda _w: dialog.response(Gtk.ResponseType.OK))
        box.pack_start(entry, False, False, 0)
        dialog.show_all()
        resp = dialog.run()
        name = entry.get_text().strip().replace(" ", "-").replace("/", "-")
        dialog.destroy()
        return name if resp == Gtk.ResponseType.OK else ""
