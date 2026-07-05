"""Write the config to disk, install helper scripts, and reload Waybar."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from dataclasses import dataclass

from waybar_configurator.io import jsonc
from waybar_configurator.io.cssgen import generate_css
from waybar_configurator.model.catalog import get_module_def
from waybar_configurator.model.config import Config

SCRIPTS_SRC_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts")


@dataclass
class ApplyResult:
    config_path: str
    css_path: str
    backups: list
    installed_scripts: list
    reloaded: bool
    waybar_running: bool
    messages: list


def default_config_dir() -> str:
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(base, "waybar")


def existing_config_path(config_dir: str | None = None) -> str | None:
    config_dir = config_dir or default_config_dir()
    for name in ("config.jsonc", "config"):
        p = os.path.join(config_dir, name)
        if os.path.exists(p):
            return p
    return None


def is_waybar_running() -> bool:
    return subprocess.run(["pgrep", "-x", "waybar"],
                          capture_output=True).returncode == 0


def reload_waybar() -> bool:
    """Send SIGUSR2 (live reload). Returns True if a running Waybar was signalled."""
    if not is_waybar_running():
        return False
    subprocess.run(["pkill", "--signal", "SIGUSR2", "waybar"], capture_output=True)
    return True


def start_waybar() -> None:
    if shutil.which("waybar"):
        subprocess.Popen(["waybar"], start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _backup(path: str, backups: list) -> None:
    if os.path.exists(path):
        stamp = time.strftime("%Y%m%d-%H%M%S")
        dst = f"{path}.{stamp}.bak"
        shutil.copy2(path, dst)
        backups.append(dst)


def _install_scripts(config: Config, config_dir: str) -> list:
    wanted = set()
    for bar in config.bars:
        for m in bar.all_modules():
            md = get_module_def(m.type)
            if md and md.script:
                wanted.add(md.script)
    if not wanted:
        return []
    dst_dir = os.path.join(config_dir, "scripts")
    os.makedirs(dst_dir, exist_ok=True)
    installed = []
    for name in sorted(wanted):
        src = os.path.join(SCRIPTS_SRC_DIR, name)
        if not os.path.exists(src):
            continue
        dst = os.path.join(dst_dir, name)
        if not os.path.exists(dst):  # never clobber a user-edited script
            shutil.copy2(src, dst)
        os.chmod(dst, 0o755)
        installed.append(dst)
    return installed


def write_files(config: Config, config_path: str, css_path: str,
                make_backup: bool = True) -> list:
    backups: list = []
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    if make_backup:
        _backup(config_path, backups)
        _backup(css_path, backups)
    with open(config_path, "w", encoding="utf-8") as fh:
        fh.write(jsonc.dumps(config))
    with open(css_path, "w", encoding="utf-8") as fh:
        fh.write(generate_css(config.theme, config.used_module_types()))
    return backups


def apply(config: Config, config_dir: str | None = None) -> ApplyResult:
    config_dir = config_dir or default_config_dir()
    config_path = os.path.join(config_dir, "config.jsonc")
    css_path = os.path.join(config_dir, "style.css")

    messages: list = []
    backups = write_files(config, config_path, css_path, make_backup=True)
    installed = _install_scripts(config, config_dir)

    running = is_waybar_running()
    reloaded = reload_waybar()
    if reloaded:
        messages.append("Waybar reloaded (SIGUSR2).")
    else:
        messages.append("Waybar is not running.")

    return ApplyResult(
        config_path=config_path,
        css_path=css_path,
        backups=backups,
        installed_scripts=installed,
        reloaded=reloaded,
        waybar_running=running,
        messages=messages,
    )
