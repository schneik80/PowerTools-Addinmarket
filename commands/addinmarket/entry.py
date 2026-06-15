# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IMA LLC
"""
Fusion command "Add-in Market".

Opens a pinned HTML palette that lists curated Fusion add-ins. Users
toggle individual add-ins on/off to install or remove them. The palette
reads its data from data/marketplace.json (shipped with this add-in),
persists installed state to cache/installed.json, and starts/stops
add-ins live via app.scripts without requiring a Fusion restart.
"""

import json
import os
import pathlib
import subprocess

import adsk.core
import adsk.fusion

from ... import config
from ...lib import fusionAddInUtils as futil
from . import installer

# ---------------------------------------------------------------------------
# Identity
# ---------------------------------------------------------------------------

CMD_ID = f"{config.COMPANY_NAME}_AddinMarket"
CMD_NAME = "Add-in Market"
CMD_TOOLTIP = (
    "Browse and install Fusion add-ins from the PowerTools curated marketplace."
)
PALETTE_ID = f"{config.COMPANY_NAME}_AddinMarket_Palette"
PALETTE_NAME = "Add-in Market"

IS_PROMOTED = True
WORKSPACE_ID = config.design_workspace
TAB_ID = config.tools_tab_id
PANEL_ID = config.my_panel_id

ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "")
PALETTE_HTML = pathlib.Path(
    os.path.dirname(os.path.abspath(__file__)),
    "resources", "palette", "marketplace.html",
).as_uri()

app: adsk.core.Application
ui: adsk.core.UserInterface

_palette = None

# Palette handlers must outlive the command lifecycle, so they live in this
# module-level list and are only cleared by stop() via futil.clear_handlers().
local_handlers = []


# ---------------------------------------------------------------------------
# Lifecycle
# ---------------------------------------------------------------------------

def start():
    global app, ui
    app = adsk.core.Application.get()
    ui = app.userInterface

    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if cmd_def:
        cmd_def.deleteMe()

    cmd_def = ui.commandDefinitions.addButtonDefinition(
        CMD_ID, CMD_NAME, CMD_TOOLTIP, ICON_FOLDER
    )
    futil.add_handler(cmd_def.commandCreated, command_created)

    panel = futil.get_or_create_panel(WORKSPACE_ID, TAB_ID, config.my_tab_name, PANEL_ID, config.my_panel_name, config.my_panel_after)
    if panel:
        ctl = panel.controls.itemById(CMD_ID)
        if ctl:
            ctl.deleteMe()
        ctl = panel.controls.addCommand(cmd_def)
        ctl.isPromoted = IS_PROMOTED


def stop():
    global _palette

    futil.remove_from_panel(WORKSPACE_ID, PANEL_ID, TAB_ID, CMD_ID)
    cmd_def = ui.commandDefinitions.itemById(CMD_ID)
    if cmd_def:
        cmd_def.deleteMe()

    pal = ui.palettes.itemById(PALETTE_ID)
    if pal:
        pal.deleteMe()
    _palette = None


# ---------------------------------------------------------------------------
# Command created — show palette here, before command execution completes.
# Palette handlers are registered in local_handlers which is NOT cleared on
# command_destroy, so the incomingFromHTML bridge stays alive.
# ---------------------------------------------------------------------------

def command_created(args: adsk.core.CommandCreatedEventArgs):
    futil.log(f"{CMD_NAME} Command Created")
    _show_palette()

    # Attach a no-op execute so Fusion's command lifecycle completes cleanly.
    futil.add_handler(args.command.execute, command_execute,
                      local_handlers=local_handlers)
    args.command.isExecutedWhenPreEmpted = False


def command_execute(args: adsk.core.CommandEventArgs):
    # Palette was already shown in command_created.
    pass


# ---------------------------------------------------------------------------
# Palette management
# ---------------------------------------------------------------------------

def _show_palette():
    """Create the palette on first use or re-show it if it already exists."""
    global _palette
    _palette = ui.palettes.itemById(PALETTE_ID)

    if _palette is None:
        _palette = ui.palettes.add(
            PALETTE_ID,
            PALETTE_NAME,
            PALETTE_HTML,
            True,   # isVisible
            True,   # showCloseButton
            True,   # isResizable
            700,    # width
            540,    # height
        )
        futil.add_handler(_palette.incomingFromHTML, palette_incoming,
                          local_handlers=local_handlers)
        futil.add_handler(_palette.closed, palette_closed,
                          local_handlers=local_handlers)

    if _palette.dockingState == adsk.core.PaletteDockingStates.PaletteDockStateFloating:
        _palette.dockingState = adsk.core.PaletteDockingStates.PaletteDockStateRight

    _palette.isVisible = True
    _palette.sendInfoToHTML("setTheme", _fusion_theme())


def palette_closed(args: adsk.core.UserInterfaceGeneralEventArgs):
    futil.log(f"{CMD_NAME} palette closed")


def _fusion_theme() -> str:
    """Return 'dark' or 'light' matching Fusion's active UI theme.

    Uses activeUserInterfaceTheme so the DeviceUserInterfaceTheme setting
    (follow OS) is resolved to the actual applied theme before comparison.
    """
    try:
        theme = app.preferences.generalPreferences.activeUserInterfaceTheme
        _dark = {
            adsk.core.UserInterfaceThemes.DarkBlueUserInterfaceTheme,
            adsk.core.UserInterfaceThemes.DarkGrayUserInterfaceTheme,
        }
        return "dark" if theme in _dark else "light"
    except Exception:
        return "dark"


# ---------------------------------------------------------------------------
# Palette events — JSON-RPC bridge
# ---------------------------------------------------------------------------

def palette_incoming(args: adsk.core.HTMLEventArgs):
    """Dispatch JSON-RPC envelopes from the HTML palette."""
    try:
        envelope = json.loads(args.data) if args.data else {}
    except ValueError:
        return

    rpc_id = envelope.get("id")
    method  = envelope.get("method", "")
    params  = envelope.get("params") or {}

    futil.log(f"{CMD_NAME} RPC: {method}")

    try:
        if method == "getTheme":
            _reply(rpc_id, True, _fusion_theme())

        elif method == "listAddins":
            _reply(rpc_id, True, _rpc_list_addins(params))

        elif method == "install":
            _reply(rpc_id, True, _rpc_install(params))

        elif method == "uninstall":
            _reply(rpc_id, True, _rpc_uninstall(params))

        elif method == "openReadme":
            _reply(rpc_id, True, _rpc_open_readme(params))

        else:
            _reply(rpc_id, False, f"Unknown method: {method}")

    except Exception as exc:
        futil.handle_error(f"{CMD_NAME} RPC")
        _reply(rpc_id, False, str(exc))


# ---------------------------------------------------------------------------
# RPC handlers
# ---------------------------------------------------------------------------

def _rpc_list_addins(params: dict) -> list:
    """Return add-ins for the requested tab, merged with installed state."""
    tab = params.get("tab", "core")
    marketplace = config.load_marketplace()
    installed   = config.load_installed()

    result = []
    for entry in marketplace.get(tab, []):
        addin_id         = entry["id"]
        inst             = installed.get(addin_id)
        installed_version = inst["version"] if inst else None
        manifest_version  = entry.get("version", "")

        result.append({
            "id":               addin_id,
            "name":             entry.get("name", addin_id),
            "description":      entry.get("description", ""),
            "publisher":        entry.get("publisher", ""),
            "license":          entry.get("license", ""),
            "github_repo":      entry.get("github_repo", ""),
            "version":          manifest_version,
            "readme_url":       entry.get("readme_url", ""),
            "installed":        inst is not None,
            "installed_version": installed_version,
            "update_available": (
                inst is not None
                and bool(installed_version)
                and installed_version != manifest_version
            ),
        })
    return result


def _rpc_install(params: dict) -> dict:
    """Download and install an add-in, update installed cache."""
    addin_id    = params.get("id", "")
    marketplace = config.load_marketplace()

    all_entries = marketplace.get("core", []) + marketplace.get("community", [])
    entry = next((e for e in all_entries if e["id"] == addin_id), None)
    if not entry:
        raise ValueError(f"Add-in '{addin_id}' not found in marketplace manifest")

    return installer.install(entry)


def _rpc_uninstall(params: dict) -> dict:
    """Remove an installed add-in and update the cache."""
    return installer.uninstall(params.get("id", ""))


def _rpc_open_readme(params: dict) -> dict:
    """Open the add-in's GitHub readme in the system browser."""
    import sys
    url = params.get("url", "")
    if not url:
        raise ValueError("No URL provided")
    if sys.platform == "darwin":
        subprocess.Popen(["open", url])
    else:
        subprocess.Popen(["start", url], shell=True)
    return {"ok": True}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _reply(rpc_id, ok: bool, payload):
    """Send a JSON-RPC reply back to the palette's JS."""
    if _palette is None:
        return
    msg = {"id": rpc_id, "ok": ok}
    if ok:
        msg["result"] = payload
    else:
        msg["error"] = str(payload)
    _palette.sendInfoToHTML("rpcReply", json.dumps(msg))
