"""Main application window: bar sidebar + per-bar editor notebook + actions."""

from __future__ import annotations

import os

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from waybar_configurator.io import applier, jsonc
from waybar_configurator.io.cssgen import generate_css
from waybar_configurator.model.config import Bar, Config, ModuleInstance
from waybar_configurator.ui.appearance_panel import AppearancePanel
from waybar_configurator.ui.bar_list import BarSidebar
from waybar_configurator.ui.layout_panel import LayoutPanel
from waybar_configurator.ui.modules_panel import ModulesPanel
from waybar_configurator.ui.preview import BarPreview

APP_TITLE = "Waybar Configurator"


class AppWindow(Gtk.ApplicationWindow):
    def __init__(self, app, initial_config_path=None):
        super().__init__(application=app, title=APP_TITLE)
        self.set_default_size(1040, 720)
        self._dirty = False
        self._loading = False
        self.current_index = 0
        self.source_path = initial_config_path

        self._build_headerbar()
        self._build_body()

        self._load_initial()
        self.show_all()

    # ── header ────────────────────────────────────────────────────────────────
    def _build_headerbar(self):
        hb = Gtk.HeaderBar()
        hb.set_show_close_button(True)
        hb.props.title = APP_TITLE
        self.set_titlebar(hb)
        self.headerbar = hb

        apply_btn = Gtk.Button(label="Apply to Waybar")
        apply_btn.get_style_context().add_class("suggested-action")
        apply_btn.set_tooltip_text("Write ~/.config/waybar and reload Waybar (backs up first)")
        apply_btn.connect("clicked", lambda _b: self._on_apply())
        hb.pack_end(apply_btn)

        menu_btn = Gtk.MenuButton()
        menu_btn.set_tooltip_text("More actions")
        menu_btn.set_image(Gtk.Image.new_from_icon_name("open-menu-symbolic", Gtk.IconSize.BUTTON))
        menu = Gtk.Menu()
        for label, cb in [
            ("Preview generated files", self._on_preview),
            ("Save to folder…", self._on_save_as),
            ("Reload from disk", self._on_reload_disk),
        ]:
            item = Gtk.MenuItem(label=label)
            item.connect("activate", lambda _i, f=cb: f())
            menu.append(item)
        menu.show_all()
        menu_btn.set_popup(menu)
        hb.pack_end(menu_btn)

        # Preview is a common action — surface it as its own button rather than
        # burying it in the overflow menu.
        preview_btn = Gtk.Button.new_from_icon_name("document-print-preview-symbolic",
                                                    Gtk.IconSize.BUTTON)
        preview_btn.set_tooltip_text("Preview the generated config.jsonc and style.css")
        preview_btn.connect("clicked", lambda _b: self._on_preview())
        hb.pack_end(preview_btn)

        # A left-aligned hint of which file is being edited.
        self.subtitle_label = Gtk.Label()
        self.subtitle_label.get_style_context().add_class("dim-label")
        hb.pack_start(self.subtitle_label)

    # ── body ──────────────────────────────────────────────────────────────────
    def _build_body(self):
        self.paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        self.paned.set_position(220)

        self.sidebar = BarSidebar(
            on_select=self._on_bar_selected,
            on_add=self._on_add_bar,
            on_duplicate=self._on_duplicate_bar,
            on_delete=self._on_delete_bar,
        )
        self.paned.pack1(self.sidebar, False, False)

        self.editor_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        # Persistent live preview at the top; the tabbed editor below is swapped
        # out on every bar change, but the preview stays put.
        self.preview = None
        self.preview_holder = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.editor_container.pack_start(self.preview_holder, False, False, 0)
        self._editor_body = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.editor_container.pack_start(self._editor_body, True, True, 0)
        self.paned.pack2(self.editor_container, True, False)

        self.add(self.paned)

    # ── loading / state ───────────────────────────────────────────────────────
    def _load_initial(self):
        path = self.source_path or applier.existing_config_path()
        cfg = None
        if path and os.path.exists(path):
            try:
                cfg = jsonc.load_config(path)
                self.source_path = path
            except Exception as exc:  # noqa: BLE001
                self._error(f"Could not read {path}:\n{exc}\n\nStarting from a default bar.")
        if cfg is None or not cfg.bars:
            cfg = Config.default()
        self.config = cfg
        self.sidebar.set_config(self.config)
        self._attach_preview()
        self.current_index = 0
        self.sidebar.refresh(select_index=0)
        self._set_dirty(False)

    def _attach_preview(self):
        """Create the preview (first load) or point it at the reloaded config."""
        if self.preview is None:
            self.preview = BarPreview(self.config, 0)
            self.preview_holder.pack_start(self.preview, False, False, 0)
            self.preview_holder.show_all()
        else:
            self.preview.config = self.config
            self.preview.set_bar_index(0)

    def _refresh_preview(self):
        if self.preview is not None:
            self.preview.refresh()

    def _mark_layout_changed(self):
        self._set_dirty(True)
        self._refresh_sidebar_labels()
        self._refresh_preview()

    def _mark_content_changed(self):
        self._set_dirty(True)
        self._refresh_preview()

    def _refresh_sidebar_labels(self):
        self._loading = True
        self.sidebar.refresh(select_index=self.current_index)
        self._loading = False

    def _set_dirty(self, dirty):
        self._dirty = dirty
        self.headerbar.props.title = APP_TITLE + (" •" if dirty else "")
        self._update_header_subtitle()

    def _update_header_subtitle(self):
        if self.source_path:
            base = os.path.basename(self.source_path)
            text = f"{base} • unsaved" if self._dirty else base
        else:
            text = "new configuration • unsaved" if self._dirty else "new configuration"
        self.subtitle_label.set_text(text)

    # ── editor rebuild ────────────────────────────────────────────────────────
    def _rebuild_editor(self):
        for child in self._editor_body.get_children():
            self._editor_body.remove(child)
        if self.preview is not None:
            self.preview.set_bar_index(self.current_index)
        if not self.config.bars:
            self._editor_body.pack_start(
                Gtk.Label(label="No bars. Click + to add one."), True, True, 0)
            self._editor_body.show_all()
            return

        bar = self.config.bars[self.current_index]
        notebook = Gtk.Notebook()
        notebook.set_border_width(6)

        layout = LayoutPanel(bar, self._mark_layout_changed)
        notebook.append_page(self._scroll(layout), Gtk.Label(label="Layout"))

        modules = ModulesPanel(bar, self._mark_content_changed)
        notebook.append_page(modules, Gtk.Label(label="Modules"))

        appearance = AppearancePanel(self.config, self._mark_content_changed)
        notebook.append_page(appearance, Gtk.Label(label="Appearance"))

        self._editor_body.pack_start(notebook, True, True, 0)
        self._editor_body.show_all()

    @staticmethod
    def _scroll(child):
        sw = Gtk.ScrolledWindow()
        sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sw.add(child)
        return sw

    # ── bar actions ───────────────────────────────────────────────────────────
    def _on_bar_selected(self, index):
        if self._loading:
            return
        self.current_index = index
        self._rebuild_editor()

    def _on_add_bar(self):
        n = len(self.config.bars) + 1
        bar = Bar(name=f"Bar {n}", position="bottom")
        bar.modules_left = [ModuleInstance("clock")]
        self.config.bars.append(bar)
        self.current_index = len(self.config.bars) - 1
        self.sidebar.refresh(select_index=self.current_index)
        self._set_dirty(True)

    def _on_duplicate_bar(self):
        if not self.config.bars:
            return
        clone = self.config.bars[self.current_index].clone()
        clone.name += " copy"
        self.config.bars.insert(self.current_index + 1, clone)
        self.current_index += 1
        self.sidebar.refresh(select_index=self.current_index)
        self._set_dirty(True)

    def _on_delete_bar(self):
        if len(self.config.bars) <= 1:
            self._error("A Waybar config needs at least one bar.")
            return
        bar = self.config.bars[self.current_index]
        if not self._confirm(f"Delete bar “{bar.name}”?"):
            return
        self.config.bars.pop(self.current_index)
        self.current_index = max(0, self.current_index - 1)
        self.sidebar.refresh(select_index=self.current_index)
        self._set_dirty(True)

    # ── apply / save ──────────────────────────────────────────────────────────
    def _on_apply(self):
        try:
            result = applier.apply(self.config)
        except Exception as exc:  # noqa: BLE001
            self._error(f"Apply failed:\n{exc}")
            return
        self._set_dirty(False)

        lines = [
            f"Wrote {result.config_path}",
            f"Wrote {result.css_path}",
        ]
        if result.backups:
            lines.append(f"Backed up {len(result.backups)} file(s).")
        if result.installed_scripts:
            lines.append(f"Installed {len(result.installed_scripts)} helper script(s).")
        lines.append("")
        lines.extend(result.messages)

        if not result.waybar_running:
            if self._confirm("\n".join(lines) + "\n\nWaybar isn't running. Start it now?"):
                applier.start_waybar()
        else:
            self._info("Applied", "\n".join(lines))

    def _on_save_as(self):
        dialog = Gtk.FileChooserDialog(
            title="Choose a folder to save config.jsonc and style.css",
            transient_for=self, action=Gtk.FileChooserAction.SELECT_FOLDER)
        dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Save", Gtk.ResponseType.OK)
        if dialog.run() == Gtk.ResponseType.OK:
            folder = dialog.get_filename()
            dialog.destroy()
            try:
                applier.write_files(
                    self.config,
                    os.path.join(folder, "config.jsonc"),
                    os.path.join(folder, "style.css"),
                    make_backup=True,
                )
                self._info("Saved", f"Wrote config.jsonc and style.css to\n{folder}")
            except Exception as exc:  # noqa: BLE001
                self._error(f"Save failed:\n{exc}")
        else:
            dialog.destroy()

    def _on_reload_disk(self):
        path = self.source_path or applier.existing_config_path()
        if not path or not os.path.exists(path):
            self._error("No config file found on disk to reload.")
            return
        if self._dirty and not self._confirm("Discard unsaved changes and reload from disk?"):
            return
        try:
            self.config = jsonc.load_config(path)
        except Exception as exc:  # noqa: BLE001
            self._error(f"Reload failed:\n{exc}")
            return
        if not self.config.bars:
            self.config = Config.default()
        self.sidebar.set_config(self.config)
        self._attach_preview()
        self.current_index = 0
        self.sidebar.refresh(select_index=0)
        self._set_dirty(False)

    def _on_preview(self):
        cfg_text = jsonc.dumps(self.config)
        css_text = generate_css(self.config.theme, self.config.used_module_types())
        dialog = Gtk.Dialog(title="Generated output", transient_for=self, modal=True)
        dialog.set_default_size(720, 560)
        dialog.add_button("Close", Gtk.ResponseType.CLOSE)
        nb = Gtk.Notebook()
        nb.append_page(self._text_page(cfg_text), Gtk.Label(label="config.jsonc"))
        nb.append_page(self._text_page(css_text), Gtk.Label(label="style.css"))
        dialog.get_content_area().pack_start(nb, True, True, 0)
        dialog.show_all()
        dialog.run()
        dialog.destroy()

    @staticmethod
    def _text_page(text):
        view = Gtk.TextView()
        view.set_editable(False)
        view.set_monospace(True)
        view.get_buffer().set_text(text)
        sw = Gtk.ScrolledWindow()
        sw.add(view)
        return sw

    # ── dialogs ───────────────────────────────────────────────────────────────
    def _confirm(self, message):
        d = Gtk.MessageDialog(transient_for=self, modal=True,
                              message_type=Gtk.MessageType.QUESTION,
                              buttons=Gtk.ButtonsType.OK_CANCEL, text=message)
        resp = d.run()
        d.destroy()
        return resp == Gtk.ResponseType.OK

    def _info(self, title, message):
        d = Gtk.MessageDialog(transient_for=self, modal=True,
                              message_type=Gtk.MessageType.INFO,
                              buttons=Gtk.ButtonsType.OK, text=title)
        d.format_secondary_text(message)
        d.run()
        d.destroy()

    def _error(self, message):
        d = Gtk.MessageDialog(transient_for=self, modal=True,
                              message_type=Gtk.MessageType.ERROR,
                              buttons=Gtk.ButtonsType.OK, text="Error")
        d.format_secondary_text(message)
        d.run()
        d.destroy()
