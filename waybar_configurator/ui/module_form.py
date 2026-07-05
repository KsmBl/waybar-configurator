"""Dynamic settings form generated from a module's catalog schema."""

from __future__ import annotations

import json

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from waybar_configurator.model.catalog import ACTION_KEYS, action_fields_for, get_module_def
from waybar_configurator.ui import widgets


def _multiline(text: str, height: int = 70) -> tuple:
    view = Gtk.TextView()
    view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
    view.get_buffer().set_text(text)
    sw = Gtk.ScrolledWindow()
    sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
    sw.set_size_request(-1, height)
    sw.set_shadow_type(Gtk.ShadowType.IN)
    sw.add(view)
    return view, sw


def _buffer_text(view: Gtk.TextView) -> str:
    buf = view.get_buffer()
    return buf.get_text(buf.get_start_iter(), buf.get_end_iter(), True)


class ModuleForm(Gtk.Box):
    def __init__(self, instance, on_changed):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.set_border_width(12)
        self.instance = instance
        self._on_changed = on_changed
        self._build()

    def _notify(self, *_):
        if self._on_changed:
            self._on_changed()

    def _build(self):
        md = get_module_def(self.instance.type)
        title = Gtk.Label(xalign=0.0)
        name = md.name if md else self.instance.type
        title.set_markup(f"<big><b>{widgets._escape(name)}</b></big>")
        self.pack_start(title, False, False, 0)

        subtitle = Gtk.Label(xalign=0.0)
        desc = (md.description if md else "") or ""
        subtitle.set_markup(
            f"<span alpha='70%'>{widgets._escape(self.instance.type)}"
            + (f" — {widgets._escape(desc)}" if desc else "")
            + "</span>"
        )
        subtitle.set_line_wrap(True)
        self.pack_start(subtitle, False, False, 0)

        if md and not md.native:
            self.pack_start(
                widgets.info_bar(
                    "Script-backed module. Its helper script is installed into "
                    "~/.config/waybar/scripts/ when you apply."
                ),
                False, False, 0,
            )

        if md:
            grid_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            for f in md.fields:
                if f.key in ACTION_KEYS:
                    continue  # rendered in the "Click & scroll actions" section below
                row = self._field_row(f)
                if row is not None:
                    grid_box.pack_start(row, False, False, 0)
            self.pack_start(grid_box, False, False, 0)
        else:
            self.pack_start(
                Gtk.Label(label="No predefined settings for this module type — "
                                "use the actions below or edit it as raw JSON.", xalign=0.0),
                False, False, 0,
            )

        # ── Click & scroll actions (available for every module) ───────────────
        frame, box = widgets.section_frame("Click & scroll actions")
        hint = Gtk.Label(xalign=0.0)
        hint.set_markup("<small><span alpha='70%'>Run a command or script when the module "
                        "is clicked or scrolled.</span></small>")
        hint.set_line_wrap(True)
        box.pack_start(hint, False, False, 0)
        for f in action_fields_for(md):
            box.pack_start(self._field_row(f), False, False, 0)
        self.pack_start(frame, False, False, 0)

    # ── one row per field ─────────────────────────────────────────────────────
    def _current(self, f):
        return self.instance.settings.get(f.key, f.default)

    def _set(self, key, value):
        self.instance.settings[key] = value
        self._notify()

    def _field_row(self, f):
        kind = f.kind
        current = self._current(f)

        if kind == "bool":
            sw = Gtk.Switch()
            sw.set_halign(Gtk.Align.START)
            sw.set_active(bool(current))
            sw.connect("notify::active", lambda w, _p: self._set(f.key, w.get_active()))
            return widgets.labelled_row(f.label, sw, f.tooltip)

        if kind in ("int", "float"):
            is_float = kind == "float"
            adj = Gtk.Adjustment(
                value=float(current) if current not in (None, "") else 0,
                lower=-100000, upper=1000000,
                step_increment=0.5 if is_float else 1,
            )
            spin = Gtk.SpinButton(adjustment=adj, digits=1 if is_float else 0)
            spin.set_halign(Gtk.Align.START)
            spin.set_size_request(120, -1)

            def _on_spin(w, key=f.key, isf=is_float):
                self._set(key, w.get_value() if isf else int(w.get_value()))

            spin.connect("value-changed", _on_spin)
            return widgets.labelled_row(f.label, spin, f.tooltip)

        if kind == "enum":
            combo = Gtk.ComboBoxText()
            for choice in (f.choices or []):
                combo.append(choice or "__empty__", choice or "(none)")
            combo.set_active_id((current or "__empty__"))
            combo.connect(
                "changed",
                lambda w, key=f.key: self._set(
                    key, "" if w.get_active_id() == "__empty__" else (w.get_active_id() or "")
                ),
            )
            return widgets.labelled_row(f.label, combo, f.tooltip)

        if kind == "text":
            view, sw = _multiline(str(current or ""))
            view.get_buffer().connect(
                "changed", lambda b, key=f.key, v=view: self._set(key, _buffer_text(v))
            )
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            lbl = Gtk.Label(label=f.label, xalign=0.0)
            box.pack_start(lbl, False, False, 0)
            box.pack_start(sw, False, False, 0)
            if f.tooltip:
                box.set_tooltip_text(f.tooltip)
            return box

        if kind == "list":
            text = "\n".join(str(x) for x in (current or []))
            view, sw = _multiline(text)
            view.get_buffer().connect(
                "changed",
                lambda b, key=f.key, v=view: self._set(key, self._parse_list(_buffer_text(v))),
            )
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            box.pack_start(Gtk.Label(label=f"{f.label} (one per line)", xalign=0.0), False, False, 0)
            box.pack_start(sw, False, False, 0)
            if f.tooltip:
                box.set_tooltip_text(f.tooltip)
            return box

        if kind in ("dict", "states"):
            text = self._dict_to_text(current or {}, numeric=(kind == "states"))
            view, sw = _multiline(text)
            view.get_buffer().connect(
                "changed",
                lambda b, key=f.key, v=view, k=kind: self._set(
                    key, self._parse_dict(_buffer_text(v), numeric=(k == "states"))
                ),
            )
            box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            hint = "name: number" if kind == "states" else "key: value"
            box.pack_start(Gtk.Label(label=f"{f.label}  ({hint}, one per line)", xalign=0.0),
                          False, False, 0)
            box.pack_start(sw, False, False, 0)
            if f.tooltip:
                box.set_tooltip_text(f.tooltip)
            return box

        # default: single-line string
        entry = Gtk.Entry()
        entry.set_text("" if current is None else str(current))
        if f.placeholder:
            entry.set_placeholder_text(f.placeholder)
        entry.connect("changed", lambda w, key=f.key: self._set(key, w.get_text()))
        return widgets.labelled_row(f.label, entry, f.tooltip)

    # ── parsing helpers ───────────────────────────────────────────────────────
    @staticmethod
    def _parse_list(text):
        return [ln.strip() for ln in text.splitlines() if ln.strip()]

    @staticmethod
    def _dict_to_text(d, numeric=False):
        lines = []
        for k, v in d.items():
            if numeric:
                lines.append(f"{k}: {v}")
            else:
                lines.append(f"{k}: {json.dumps(v, ensure_ascii=False)}")
        return "\n".join(lines)

    @staticmethod
    def _parse_dict(text, numeric=False):
        out = {}
        for ln in text.splitlines():
            if ":" not in ln:
                continue
            k, _, v = ln.partition(":")
            k, v = k.strip().strip('"'), v.strip()
            if not k:
                continue
            if numeric:
                try:
                    out[k] = int(v)
                except ValueError:
                    try:
                        out[k] = float(v)
                    except ValueError:
                        continue
            else:
                try:
                    out[k] = json.loads(v)
                except (ValueError, json.JSONDecodeError):
                    out[k] = v.strip('"')
        return out
