"""Sidebar listing all bars, with add / duplicate / delete actions."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402


class BarSidebar(Gtk.Box):
    def __init__(self, on_select, on_add, on_duplicate, on_delete):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.set_border_width(8)
        self.set_size_request(210, -1)
        self._on_select = on_select
        self.config = None

        title = Gtk.Label(xalign=0.0)
        title.set_markup("<b>Bars</b>")
        self.pack_start(title, False, False, 0)

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.connect("row-selected", self._row_selected)
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sw.set_shadow_type(Gtk.ShadowType.IN)
        sw.add(self.listbox)
        self.pack_start(sw, True, True, 0)

        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        add = Gtk.Button.new_from_icon_name("list-add-symbolic", Gtk.IconSize.BUTTON)
        add.set_tooltip_text("New bar")
        add.connect("clicked", lambda _b: on_add())
        dup = Gtk.Button.new_from_icon_name("edit-copy-symbolic", Gtk.IconSize.BUTTON)
        dup.set_tooltip_text("Duplicate bar")
        dup.connect("clicked", lambda _b: on_duplicate())
        rm = Gtk.Button.new_from_icon_name("list-remove-symbolic", Gtk.IconSize.BUTTON)
        rm.set_tooltip_text("Delete bar")
        rm.connect("clicked", lambda _b: on_delete())
        toolbar.pack_start(add, True, True, 0)
        toolbar.pack_start(dup, True, True, 0)
        toolbar.pack_start(rm, True, True, 0)
        self.pack_start(toolbar, False, False, 0)

    def set_config(self, config):
        self.config = config

    def refresh(self, select_index=0):
        for child in self.listbox.get_children():
            self.listbox.remove(child)
        for bar in (self.config.bars if self.config else []):
            self.listbox.add(self._make_row(bar))
        self.listbox.show_all()
        if self.config and self.config.bars:
            idx = max(0, min(select_index, len(self.config.bars) - 1))
            self.listbox.select_row(self.listbox.get_row_at_index(idx))

    def _make_row(self, bar):
        row = Gtk.ListBoxRow()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.set_border_width(6)
        name = Gtk.Label(label=bar.name, xalign=0.0)
        sub = Gtk.Label(xalign=0.0)
        loc = bar.output or "all monitors"
        sub.set_markup(f"<small><span alpha='65%'>{bar.position} · {loc}</span></small>")
        box.pack_start(name, False, False, 0)
        box.pack_start(sub, False, False, 0)
        row.add(box)
        return row

    def selected_index(self):
        row = self.listbox.get_selected_row()
        return row.get_index() if row else -1

    def _row_selected(self, _listbox, row):
        if row is not None:
            self._on_select(row.get_index())
