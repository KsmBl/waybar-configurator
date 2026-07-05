# Contributing

Thanks for your interest in improving Waybar Configurator!

## Development setup

```sh
git clone https://github.com/KsmBl/waybar-configurator
cd waybar-configurator
# System dependencies (Arch): sudo pacman -S python-gobject gtk3
./run.sh
```

## Project layout

```
waybar_configurator/
  main.py, app_window.py          # GTK application + main window
  model/  config.py, theme.py, catalog.py   # document model + module schema catalog
  io/     jsonc.py, cssgen.py, applier.py    # load/save, CSS generation, apply + reload
  ui/     bar_list, layout_panel, modules_panel, module_form, appearance_panel, widgets
  scripts/ weather.sh, disk-io.sh, net-bandwidth.sh
```

## Adding a module

The app is schema-driven. To support a new Waybar module, add one `ModuleDef` entry to
`waybar_configurator/model/catalog.py` describing its `Field`s — the settings form and the
JSON serializer are both generated from it. No UI or IO code required.

Modules with no native Waybar equivalent are delivered as `custom/*` modules backed by a helper
script in `waybar_configurator/scripts/`; reference the filename via the `ModuleDef.script` field.

## Before opening a PR

- `python3 -m compileall waybar_configurator` should pass.
- `bash -n waybar_configurator/scripts/*.sh` (and ideally `shellcheck`) should pass.
- Test the change against a real Waybar setup where possible.

Please keep new code consistent with the surrounding style.
