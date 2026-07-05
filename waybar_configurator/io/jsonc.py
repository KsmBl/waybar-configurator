"""Load and save Waybar's JSONC config, mapping to/from the document model.

Note: JSONC comments are stripped on load and NOT restored on save (documented behaviour).
Unknown module settings are preserved verbatim so hand-tuned configs survive a round-trip.
"""

from __future__ import annotations

import json
import os

from waybar_configurator.model.config import Bar, Config, ModuleInstance

# Bar-level keys we understand; everything else in a bar object that is referenced
# by a modules-* array is treated as a module's config block.
_BAR_KEYS = {
    "layer", "position", "output", "height", "width", "spacing", "name",
    "exclusive", "passthrough", "margin", "margin-top", "margin-right",
    "margin-bottom", "margin-left", "modules-left", "modules-center", "modules-right",
    "reload_style_on_change", "gtk-layer-shell", "ipc", "id", "start_hidden",
    "fixed-center", "mode",
}


# ── Comment stripping ─────────────────────────────────────────────────────────
def strip_json_comments(text: str) -> str:
    """Remove // and /* */ comments while leaving string literals untouched."""
    out = []
    i, n = 0, len(text)
    in_str = False
    while i < n:
        c = text[i]
        if in_str:
            out.append(c)
            if c == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if c == '"':
                in_str = False
            i += 1
            continue
        if c == '"':
            in_str = True
            out.append(c)
            i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            i += 2
            while i < n and text[i] not in "\r\n":
                i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "*":
            i += 2
            while i + 1 < n and not (text[i] == "*" and text[i + 1] == "/"):
                i += 1
            i += 2
            continue
        out.append(c)
        i += 1
    return "".join(out)


def _remove_trailing_commas(text: str) -> str:
    import re
    return re.sub(r",(\s*[}\]])", r"\1", text)


# ── Loading ───────────────────────────────────────────────────────────────────
def load_config(path: str) -> Config:
    with open(path, "r", encoding="utf-8") as fh:
        raw = fh.read()
    data = json.loads(_remove_trailing_commas(strip_json_comments(raw)))
    bar_dicts = data if isinstance(data, list) else [data]

    bars = [_bar_from_dict(bd, idx) for idx, bd in enumerate(bar_dicts)]
    cfg = Config(bars=bars)

    # Best-effort import of theme colours from a sibling style.css.
    css_path = os.path.join(os.path.dirname(path), "style.css")
    if os.path.exists(css_path):
        from waybar_configurator.io.cssgen import theme_from_css
        try:
            cfg.theme = theme_from_css(open(css_path, encoding="utf-8").read())
        except Exception:
            pass  # fall back to default theme
    return cfg


def _parse_margins(bd: dict, bar: Bar) -> None:
    for side in ("top", "right", "bottom", "left"):
        key = f"margin-{side}"
        if key in bd:
            setattr(bar, f"margin_{side}", int(bd[key]))
    if "margin" in bd and isinstance(bd["margin"], str):
        parts = bd["margin"].replace("px", "").split()
        try:
            nums = [int(p) for p in parts]
        except ValueError:
            nums = []
        if len(nums) == 1:
            bar.margin_top = bar.margin_right = bar.margin_bottom = bar.margin_left = nums[0]
        elif len(nums) == 2:
            bar.margin_top = bar.margin_bottom = nums[0]
            bar.margin_right = bar.margin_left = nums[1]
        elif len(nums) == 4:
            bar.margin_top, bar.margin_right, bar.margin_bottom, bar.margin_left = nums


def _bar_from_dict(bd: dict, idx: int) -> Bar:
    bar = Bar()
    bar.name = str(bd.get("name") or f"Bar {idx + 1}")
    bar.position = bd.get("position", "top")
    bar.output = bd.get("output", "") if isinstance(bd.get("output", ""), str) else ""
    bar.layer = bd.get("layer", "top")
    bar.height = int(bd.get("height", 0) or 0)
    bar.width = int(bd.get("width", 0) or 0)
    bar.spacing = int(bd.get("spacing", 4) or 0)
    bar.exclusive = bool(bd.get("exclusive", True))
    bar.passthrough = bool(bd.get("passthrough", False))
    _parse_margins(bd, bar)

    for placement in ("left", "center", "right"):
        names = bd.get(f"modules-{placement}", []) or []
        instances = []
        for name in names:
            if not isinstance(name, str):
                continue
            block = bd.get(name, {})
            settings = dict(block) if isinstance(block, dict) else {}
            instances.append(ModuleInstance(type=name, settings=settings))
        setattr(bar, f"modules_{placement}", instances)
    return bar


# ── Serialising ───────────────────────────────────────────────────────────────
def _is_empty(value) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _bar_to_dict(bar: Bar, include_name: bool) -> dict:
    d: dict = {}
    d["layer"] = bar.layer
    d["position"] = bar.position
    if bar.output:
        d["output"] = bar.output
    if include_name:
        d["name"] = bar.name
    if bar.height > 0:
        d["height"] = bar.height
    if bar.width > 0:
        d["width"] = bar.width
    for side in ("top", "right", "bottom", "left"):
        val = getattr(bar, f"margin_{side}")
        if val:
            d[f"margin-{side}"] = val
    d["spacing"] = bar.spacing
    if not bar.exclusive:
        d["exclusive"] = False
    if bar.passthrough:
        d["passthrough"] = True

    for placement in ("left", "center", "right"):
        mods = bar.modules_for(placement)
        if mods:
            d[f"modules-{placement}"] = [m.type for m in mods]

    # Emit each unique module's config block (first occurrence wins).
    seen = set()
    for m in bar.all_modules():
        if m.type in seen:
            continue
        seen.add(m.type)
        block = {k: v for k, v in m.settings.items() if not _is_empty(v)}
        if block:
            d[m.type] = block
    return d


def dumps(config: Config) -> str:
    include_name = len(config.bars) > 1
    if len(config.bars) == 1:
        payload = _bar_to_dict(config.bars[0], include_name=False)
    else:
        payload = [_bar_to_dict(b, include_name=True) for b in config.bars]
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
