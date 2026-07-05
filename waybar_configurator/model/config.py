"""Document model: the in-memory representation the whole app edits."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

from waybar_configurator.model.catalog import get_module_def
from waybar_configurator.model.theme import Theme

PLACEMENTS = ("left", "center", "right")


def _is_empty(value) -> bool:
    return value is None or value == "" or value == [] or value == {}


def new_module_instance(module_type: str) -> "ModuleInstance":
    """Create a module instance pre-seeded with its catalog defaults, so the
    generated config is WYSIWYG rather than relying on Waybar's built-in defaults."""
    import copy as _copy

    md = get_module_def(module_type)
    settings = {}
    if md:
        for f in md.fields:
            if not _is_empty(f.default):
                settings[f.key] = _copy.deepcopy(f.default)
    return ModuleInstance(type=module_type, settings=settings)


@dataclass
class ModuleInstance:
    """One placed module: a Waybar module key plus its (non-default) settings."""

    type: str  # e.g. "clock", "cpu#1", "custom/weather"
    settings: dict = field(default_factory=dict)

    @property
    def base_type(self) -> str:
        return self.type.split("#", 1)[0]

    @property
    def suffix(self) -> str:
        return self.type.split("#", 1)[1] if "#" in self.type else ""

    def display_name(self) -> str:
        md = get_module_def(self.type)
        label = md.name if md else self.type
        return f"{label}  ·  {self.suffix}" if self.suffix else label

    def icon(self) -> str:
        md = get_module_def(self.type)
        return md.icon if md else "󰐕"

    def clone(self) -> "ModuleInstance":
        return ModuleInstance(self.type, copy.deepcopy(self.settings))


@dataclass
class Bar:
    name: str = "Bar"
    position: str = "top"  # top | bottom | left | right
    output: str = ""  # monitor name, "" = all monitors
    layer: str = "top"  # top | bottom | overlay
    height: int = 0  # 0 = auto
    width: int = 0  # 0 = auto / stretch
    margin_top: int = 0
    margin_right: int = 0
    margin_bottom: int = 0
    margin_left: int = 0
    spacing: int = 4
    exclusive: bool = True
    passthrough: bool = False
    modules_left: list = field(default_factory=list)
    modules_center: list = field(default_factory=list)
    modules_right: list = field(default_factory=list)

    def modules_for(self, placement: str) -> list:
        return getattr(self, f"modules_{placement}")

    def all_modules(self):
        for p in PLACEMENTS:
            yield from self.modules_for(p)

    def clone(self) -> "Bar":
        b = copy.copy(self)
        for p in PLACEMENTS:
            setattr(b, f"modules_{p}", [m.clone() for m in self.modules_for(p)])
        return b


@dataclass
class Config:
    bars: list = field(default_factory=list)
    theme: Theme = field(default_factory=Theme)

    def used_module_types(self) -> set:
        """Base module types present across all bars (for CSS generation)."""
        types = set()
        for bar in self.bars:
            for m in bar.all_modules():
                types.add(m.base_type)
        return types

    @staticmethod
    def default() -> "Config":
        bar = Bar(name="Main bar")
        bar.modules_left = [ModuleInstance("clock")]
        bar.modules_right = [
            ModuleInstance("cpu"),
            ModuleInstance("memory"),
            ModuleInstance("pulseaudio"),
            ModuleInstance("battery"),
        ]
        return Config(bars=[bar], theme=Theme())
