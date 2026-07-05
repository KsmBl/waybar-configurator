"""Module catalog — the single source of truth for every supported Waybar module.

Each :class:`ModuleDef` describes a module type and a schema of :class:`Field` objects.
The UI (``ui/module_form.py``) renders a settings form from the schema, and the serializer
(``io/jsonc.py``) emits JSON from the same schema — so adding a new module type is just a new
entry here, no UI or IO code required.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

# ── Field kinds understood by the form builder / serializer ───────────────────
#   str    single-line text            -> JSON string
#   text   multi-line text             -> JSON string
#   int    integer spin button         -> JSON number
#   float  float spin button           -> JSON number
#   bool   switch                      -> JSON bool
#   enum   dropdown (needs `choices`)  -> JSON string
#   list   list of strings (one/line)  -> JSON array
#   dict   key:value string map        -> JSON object
#   states name:threshold map          -> JSON object of numbers


@dataclass
class Field:
    key: str
    label: str
    kind: str = "str"
    default: Any = None
    tooltip: str = ""
    choices: Optional[list] = None
    placeholder: str = ""


@dataclass
class ModuleDef:
    key: str  # Waybar module key, e.g. "clock" or "custom/weather"
    name: str  # human-readable label
    category: str
    icon: str  # emoji shown in the add-module picker
    native: bool = True
    fields: list = field(default_factory=list)
    # For custom modules backed by a bundled helper script:
    script: Optional[str] = None  # filename in waybar_configurator/scripts/
    # For the generic custom module the user must supply an instance name:
    needs_instance_name: bool = False
    description: str = ""


# Convenience builders for the very common warning/critical fields ------------
def _states():
    return Field(
        "states",
        "States (name : %)",
        "states",
        default={"warning": 70, "critical": 90},
        tooltip="Threshold percentages that add a CSS class (e.g. .warning, .critical).",
    )


def _interval(default=2):
    return Field("interval", "Refresh interval (s)", "int", default=default,
                 tooltip="How often the module updates, in seconds.")


CATEGORIES = [
    "Time", "Hardware", "Network", "Audio", "Power", "Info", "Workspace", "Custom",
]


MODULE_CATALOG: list[ModuleDef] = [
    # ── Time ─────────────────────────────────────────────────────────────────
    ModuleDef(
        "clock", "Clock / Time", "Time", "🕒",
        description="Date and time, with an alternate format on click.",
        fields=[
            Field("format", "Format", "str", "{:%H:%M}",
                  tooltip="strftime format, e.g. {:%H:%M} or   {:%a %d %b}."),
            Field("format-alt", "Alt format (on click)", "str", "{:%A, %B %d %Y}"),
            Field("tooltip-format", "Tooltip format", "text",
                  "<big>{:%B %Y}</big>\n<tt><small>{calendar}</small></tt>"),
            _interval(1),
            Field("on-click-right", "Right-click command", "str", ""),
        ],
    ),

    # ── Hardware ─────────────────────────────────────────────────────────────
    ModuleDef(
        "cpu", "CPU usage", "Hardware", "🧠",
        description="Processor load as a percentage.",
        fields=[
            Field("format", "Format", "str", "󰍛  {usage}%"),
            Field("format-alt", "Alt format (on click)", "str", ""),
            _interval(2),
            _states(),
            Field("on-click-right", "Right-click command", "str", ""),
        ],
    ),
    ModuleDef(
        "memory", "Memory (RAM)", "Hardware", "󰘚",
        description="RAM usage, absolute or percentage.",
        fields=[
            Field("format", "Format", "str", "󰘚  {used:0.1f}G"),
            Field("format-alt", "Alt format (on click)", "str", "󰘚  {percentage}%"),
            Field("tooltip-format", "Tooltip format", "text",
                  "Used: {used:0.1f}G / {total:0.1f}G\nAvailable: {avail:0.1f}G"),
            _interval(2),
            _states(),
            Field("on-click-right", "Right-click command", "str", ""),
        ],
    ),
    ModuleDef(
        "disk", "Disk usage", "Hardware", "󰋊",
        description="Free/used space on a mounted path.",
        fields=[
            Field("path", "Mount path", "str", "/",
                  tooltip="Filesystem path to report usage for, e.g. / or /home."),
            Field("format", "Format", "str", "󰋊  {percentage_used}%"),
            Field("tooltip-format", "Tooltip format", "text",
                  "{used} used of {total} on {path}"),
            _interval(30),
            _states(),
        ],
    ),
    ModuleDef(
        "temperature", "Temperature", "Hardware", "🌡️",
        description="CPU / thermal-zone temperature.",
        fields=[
            Field("thermal-zone", "Thermal zone", "int", None,
                  tooltip="Kernel thermal zone number (see /sys/class/thermal). Leave blank for auto."),
            Field("hwmon-path", "hwmon path", "str", "",
                  tooltip="Alternatively a direct hwmon temp file path."),
            Field("format", "Format", "str", "{temperatureC}°C"),
            Field("critical-threshold", "Critical threshold (°C)", "int", 80),
            Field("format-critical", "Critical format", "str", "  {temperatureC}°C"),
            _interval(5),
        ],
    ),
    ModuleDef(
        "backlight", "Display brightness", "Hardware", "󰃠",
        description="Screen backlight level; scroll to change.",
        fields=[
            Field("format", "Format", "str", "{icon}  {percent}%"),
            Field("format-icons", "Icons (low → high)", "list", ["󰃞", "󰃟", "󰃠"]),
            Field("scroll-step", "Scroll step (%)", "float", 5.0),
        ],
    ),

    # ── Network ──────────────────────────────────────────────────────────────
    ModuleDef(
        "network", "Network", "Network", "󰤨",
        description="Wi-Fi / Ethernet status and bandwidth.",
        fields=[
            Field("format-wifi", "Wi-Fi format", "str", "󰤨  {essid} {signalStrength}%"),
            Field("format-ethernet", "Ethernet format", "str", "󰈀  {ipaddr}"),
            Field("format-disconnected", "Disconnected format", "str", "󰤭  offline"),
            Field("tooltip-format", "Tooltip format", "str",
                  "{ifname}: {ipaddr}\n↓ {bandwidthDownBits}  ↑ {bandwidthUpBits}"),
            _interval(2),
            Field("on-click-right", "Right-click command", "str", ""),
        ],
    ),

    # ── Audio ────────────────────────────────────────────────────────────────
    ModuleDef(
        "pulseaudio", "Volume (PulseAudio)", "Audio", "󰕾",
        description="Output volume with device detection.",
        fields=[
            Field("format", "Format", "str", "{icon}  {volume}%"),
            Field("format-muted", "Muted format", "str", "󰝟  muted"),
            Field("format-icons", "Icons map", "dict",
                  {"default": ["󰕿", "󰖀", "󰕾"], "headphone": "󰋋", "headset": "󰋎"}),
            Field("scroll-step", "Scroll step (%)", "float", 5.0),
            Field("on-click", "Click command", "str",
                  "pactl set-sink-mute @DEFAULT_SINK@ toggle"),
            Field("on-click-right", "Right-click command", "str", "pavucontrol"),
            Field("tooltip-format", "Tooltip format", "str", "{desc}\n{volume}%"),
        ],
    ),
    ModuleDef(
        "wireplumber", "Volume (WirePlumber)", "Audio", "󰕾",
        description="Output volume via WirePlumber/PipeWire.",
        fields=[
            Field("format", "Format", "str", "{icon}  {volume}%"),
            Field("format-muted", "Muted format", "str", "󰝟  Muted"),
            Field("format-icons", "Icons (low → high)", "list", ["󰕿", "󰖀", "󰕾"]),
            Field("scroll-step", "Scroll step (%)", "float", 5.0),
            Field("max-volume", "Max volume (%)", "int", 150),
            Field("on-click", "Click command", "str",
                  "wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle"),
        ],
    ),

    # ── Power ────────────────────────────────────────────────────────────────
    ModuleDef(
        "battery", "Battery", "Power", "󰁹",
        description="Charge level and charging state.",
        fields=[
            Field("format", "Format", "str", "{icon}  {capacity}%"),
            Field("format-charging", "Charging format", "str", "󰂄  {capacity}%"),
            Field("format-plugged", "Plugged format", "str", "󰚥  {capacity}%"),
            Field("format-alt", "Alt format (on click)", "str", "{icon}  {time}"),
            Field("format-icons", "Icons (empty → full)", "list",
                  ["󰁺", "󰁻", "󰁼", "󰁽", "󰁾", "󰁿", "󰂀", "󰂁", "󰂂", "󰁹"]),
            Field("states", "States (name : %)", "states",
                  default={"good": 90, "warning": 30, "critical": 15}),
            Field("tooltip-format", "Tooltip format", "str", "{timeTo}\n{capacity}% charged"),
        ],
    ),

    # ── Info / misc ──────────────────────────────────────────────────────────
    ModuleDef(
        "idle_inhibitor", "Idle inhibitor", "Info", "󰅶",
        description="Toggle to prevent the screen from sleeping.",
        fields=[
            Field("format", "Format", "str", "{icon}"),
            Field("format-icons", "Icons map", "dict",
                  {"activated": "󰅶", "deactivated": "󰾪"}),
        ],
    ),
    ModuleDef(
        "bluetooth", "Bluetooth", "Info", "󰂯",
        description="Bluetooth adapter and connections.",
        fields=[
            Field("format", "Format", "str", "󰂯  {status}"),
            Field("format-connected", "Connected format", "str", "󰂱  {device_alias}"),
            Field("on-click", "Click command", "str", "blueman-manager"),
            Field("tooltip-format", "Tooltip format", "str",
                  "{controller_alias}\n{num_connections} connected"),
        ],
    ),
    ModuleDef(
        "tray", "System tray", "Info", "󰀻",
        description="Status-notifier tray icons.",
        fields=[
            Field("icon-size", "Icon size (px)", "int", 18),
            Field("spacing", "Spacing (px)", "int", 8),
        ],
    ),

    # ── Workspace (compositor-specific) ──────────────────────────────────────
    ModuleDef(
        "sway/workspaces", "Workspaces (Sway)", "Workspace", "󰍹",
        description="Sway workspace buttons.",
        fields=[
            Field("disable-scroll", "Disable scroll switching", "bool", True),
            Field("all-outputs", "Show all outputs", "bool", True),
            Field("format", "Format", "str", "{icon}"),
            Field("format-icons", "Icons map", "dict",
                  {"urgent": "!", "default": "·"}),
        ],
    ),
    ModuleDef(
        "sway/mode", "Mode indicator (Sway)", "Workspace", "󰌌",
        description="Shows the active Sway binding mode.",
        fields=[Field("format", "Format", "str", "  {}")],
    ),
    ModuleDef(
        "hyprland/workspaces", "Workspaces (Hyprland)", "Workspace", "󰍹",
        description="Hyprland workspace buttons.",
        fields=[
            Field("format", "Format", "str", "{icon}"),
            Field("format-icons", "Icons map", "dict", {"active": "", "default": ""}),
        ],
    ),

    # ── Custom / script-backed ───────────────────────────────────────────────
    ModuleDef(
        "custom/weather", "Weather", "Custom", "󰖙", native=False, script="weather.sh",
        description="Current conditions via wttr.in (bundled script).",
        fields=[
            Field("exec", "Script", "str", "~/.config/waybar/scripts/weather.sh"),
            Field("return-type", "Return type", "enum", "json", choices=["json", ""]),
            _interval(900),
            Field("format", "Format", "str", "{}"),
            Field("tooltip", "Show tooltip", "bool", True),
        ],
    ),
    ModuleDef(
        "custom/disk-io", "Disk access (I/O)", "Custom", "󰀦", native=False, script="disk-io.sh",
        description="Disk read/write throughput (bundled script).",
        fields=[
            Field("exec", "Script", "str", "~/.config/waybar/scripts/disk-io.sh"),
            Field("return-type", "Return type", "enum", "json", choices=["json", ""]),
            _interval(2),
            Field("format", "Format", "str", "{}"),
            Field("tooltip", "Show tooltip", "bool", True),
        ],
    ),
    ModuleDef(
        "custom/net-bandwidth", "Network bandwidth", "Custom", "󰓅", native=False,
        script="net-bandwidth.sh",
        description="Combined up/down bandwidth (bundled script).",
        fields=[
            Field("exec", "Script", "str", "~/.config/waybar/scripts/net-bandwidth.sh"),
            Field("return-type", "Return type", "enum", "json", choices=["json", ""]),
            _interval(2),
            Field("format", "Format", "str", "{}"),
            Field("tooltip", "Show tooltip", "bool", True),
        ],
    ),
    ModuleDef(
        "custom", "Custom command…", "Custom", "󰆍", native=False, needs_instance_name=True,
        description="Run any command/script and show its output.",
        fields=[
            Field("exec", "Command / script", "str", "",
                  tooltip="Command to run. Prints text, or JSON when return-type is json."),
            Field("return-type", "Return type", "enum", "", choices=["", "json"]),
            _interval(10),
            Field("format", "Format", "str", "{}"),
            Field("on-click", "Click command", "str", ""),
            Field("tooltip", "Show tooltip", "bool", True),
        ],
    ),
]


# ── Common interaction actions available on every module ─────────────────────
# Waybar supports these click/scroll handlers on essentially all modules. They are
# rendered in a dedicated "Click & scroll actions" section of every module's form.
ACTION_KEYS = [
    "on-click", "on-click-right", "on-click-middle", "on-scroll-up", "on-scroll-down",
]

_ACTION_LABELS = {
    "on-click": ("Left click", "Command or script to run on left click."),
    "on-click-right": ("Right click", "Command or script to run on right click."),
    "on-click-middle": ("Middle click", "Command or script to run on middle click."),
    "on-scroll-up": ("Scroll up", "Command to run on scroll up (overrides any built-in scroll action)."),
    "on-scroll-down": ("Scroll down", "Command to run on scroll down (overrides any built-in scroll action)."),
}


def action_fields_for(module_def: Optional[ModuleDef]) -> list:
    """Return the action Fields for a module: reuse the module's own definition
    where it already declares one (to keep its default), else a generic blank field."""
    existing = {f.key: f for f in (module_def.fields if module_def else [])}
    result = []
    for key in ACTION_KEYS:
        if key in existing:
            result.append(existing[key])
        else:
            label, tooltip = _ACTION_LABELS[key]
            result.append(Field(key, label, "str", "", tooltip=tooltip,
                                placeholder="command or /path/to/script.sh"))
    return result


_BY_KEY = {m.key: m for m in MODULE_CATALOG}


def get_module_def(module_type: str) -> Optional[ModuleDef]:
    """Return the ModuleDef for a Waybar module key.

    Handles instance suffixes ("cpu#1" -> "cpu") and unknown custom modules
    ("custom/foo" -> the generic "custom" definition)."""
    base = module_type.split("#", 1)[0]
    if base in _BY_KEY:
        return _BY_KEY[base]
    if base.startswith("custom/"):
        return _BY_KEY.get("custom")
    return None


def field_default(module_type: str, field_key: str) -> Any:
    md = get_module_def(module_type)
    if md:
        for f in md.fields:
            if f.key == field_key:
                return f.default
    return None
