# Waybar Configurator

[![CI](https://github.com/KsmBl/waybar-configurator/actions/workflows/ci.yml/badge.svg)](https://github.com/KsmBl/waybar-configurator/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

A graphical configurator for [Waybar](https://github.com/Alexays/Waybar), built with
**Python + GTK3** (PyGObject) so it looks at home on an xfce4 desktop — it inherits your system
GTK theme rather than imposing its own.

Create and delete bars, position them (including multiple bars, even side by side), pick colours
and fonts, and add pre-defined modules (clock, CPU, memory, disk usage, disk I/O, network,
weather, brightness, volume, battery, temperature, tray, Bluetooth, workspaces, and custom
commands) — each with a graphical settings form. The tool writes Waybar's `config.jsonc` and
`style.css` and reloads Waybar live.

## Features

- **Bars** — add / duplicate / delete; set position (top/bottom/left/right), monitor, layer,
  height, width, margins, spacing, and behaviour (exclusive / click-through).
- **Multiple bars next to each other** — give each bar an `output` (monitor), or a fixed `width`
  plus margins, to place them on the same edge.
- **Modules** — three reorderable columns (left / center / right); add from a categorised picker;
  edit every module's settings through generated forms driven by a schema catalog.
- **Appearance** — guided pickers for background (with opacity), text, accent, hover and tooltip
  colours; corner radius, padding, font; plus optional per-module text-colour overrides. These
  generate a clean `style.css`.
- **Apply** — backs up your existing files, writes `~/.config/waybar/{config.jsonc,style.css}`,
  installs any needed helper scripts into `~/.config/waybar/scripts/`, and reloads Waybar
  (`SIGUSR2`). Offers to launch Waybar if it isn't running.
- **Import** — loads your current config on startup so you start from what you already have.

## Requirements

- Python ≥ 3.10
- GTK 3 + PyGObject (Arch: `sudo pacman -S python-gobject gtk3`)
- Waybar (to apply/reload)
- `curl` and `coreutils` (`numfmt`) for the bundled weather / disk-I/O / bandwidth scripts

## Run

```sh
./run.sh
# or
python3 -m waybar_configurator
# open a specific config file:
python3 -m waybar_configurator ~/.config/waybar/config.jsonc
```

## Install

Install into your environment (provides the `waybar-configurator` command):

```sh
pip install --user .
```

Optionally add a menu entry:

```sh
install -Dm644 data/waybar-configurator.desktop \
  ~/.local/share/applications/waybar-configurator.desktop
```

## How modules map to Waybar

Most modules are native Waybar modules (`clock`, `cpu`, `memory`, `disk`, `network`, `backlight`,
`pulseaudio`, `wireplumber`, `battery`, `temperature`, `tray`, `idle_inhibitor`, `bluetooth`,
`sway/*`, `hyprland/*`). Three asks have no native equivalent and are delivered as `custom/*`
modules backed by small bundled scripts, installed on apply:

| Module              | Script                        |
|---------------------|-------------------------------|
| Weather             | `scripts/weather.sh` (wttr.in) |
| Disk access (I/O)   | `scripts/disk-io.sh`          |
| Network bandwidth   | `scripts/net-bandwidth.sh`    |

Set `WEATHER_LOCATION` in your environment to override the weather script's IP-based location.

## Notes & limitations

- **JSONC comments are not preserved.** Comments in an imported `config.jsonc` are stripped and
  not written back. Your original file is backed up (`config.jsonc.<timestamp>.bak`) on apply.
- **CSS import is best-effort.** A small set of recognisable colours/sizes are read from an
  existing `style.css` to seed the Appearance controls; hand-written rules that aren't recognised
  are not round-tripped. The original `style.css` is backed up before overwrite.
- Unknown/hand-tuned **module settings are preserved** verbatim on save.

## Project layout

```
waybar_configurator/
  main.py, app_window.py          # GTK application + main window
  model/  config.py, theme.py, catalog.py   # document model + module schema catalog
  io/     jsonc.py, cssgen.py, applier.py    # load/save, CSS generation, apply+reload
  ui/     bar_list, layout_panel, modules_panel, module_form, appearance_panel, widgets
  scripts/ weather.sh, disk-io.sh, net-bandwidth.sh
```

Adding a new module type is a single entry in `model/catalog.py` — the settings form and the
serializer are both generated from its schema.

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

Released under the [MIT License](LICENSE).
