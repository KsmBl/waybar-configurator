"""Small reusable GTK3 helpers shared across the UI panels."""

from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gdk, Gtk  # noqa: E402


def hex_to_rgba(hex_str: str) -> Gdk.RGBA:
    rgba = Gdk.RGBA()
    if not rgba.parse(hex_str or "#000000"):
        rgba.parse("#000000")
    return rgba


def rgba_to_hex(rgba: Gdk.RGBA) -> str:
    return "#{:02x}{:02x}{:02x}".format(
        round(rgba.red * 255), round(rgba.green * 255), round(rgba.blue * 255)
    )


def color_button(hex_str: str, on_change) -> Gtk.ColorButton:
    btn = Gtk.ColorButton()
    btn.set_rgba(hex_to_rgba(hex_str))
    btn.connect("color-set", lambda b: on_change(rgba_to_hex(b.get_rgba())))
    return btn


def section_frame(title: str) -> tuple:
    """Return (frame, content_box) for a titled group of settings."""
    frame = Gtk.Frame(label=f" {title} ")
    frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
    box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
    box.set_border_width(10)
    frame.add(box)
    return frame, box


def labelled_row(label_text: str, control: Gtk.Widget, tooltip: str = "") -> Gtk.Box:
    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
    lbl = Gtk.Label(label=label_text, xalign=0.0)
    lbl.set_size_request(180, -1)
    lbl.set_line_wrap(True)
    if tooltip:
        lbl.set_tooltip_text(tooltip)
        control.set_tooltip_text(tooltip)
    row.pack_start(lbl, False, False, 0)
    row.pack_start(control, True, True, 0)
    return row


def _escape(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def heading(text: str) -> Gtk.Label:
    lbl = Gtk.Label(xalign=0.0)
    lbl.set_markup(f"<b>{_escape(text)}</b>")
    return lbl


def info_bar(text: str, kind=Gtk.MessageType.INFO) -> Gtk.InfoBar:
    bar = Gtk.InfoBar()
    bar.set_message_type(kind)
    bar.get_content_area().pack_start(Gtk.Label(label=text), False, False, 0)
    return bar


def scrolled(child: Gtk.Widget) -> Gtk.ScrolledWindow:
    sw = Gtk.ScrolledWindow()
    sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
    sw.add(child)
    return sw
