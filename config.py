# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IMA LLC

import os
import json
import platform

# NOTE: do not import lib.fusionAddInUtils here. general_utils reads the flags
# below at import time, so an import from this module would run against a
# half-initialised config and capture DEBUG as False permanently. general_utils
# also re-reads the flags lazily (_refresh_flags), but keeping this module free
# of that import removes the trap at the source.

# Master logging gate. DEBUG is enabled by the presence of a ``.debug`` marker
# file in the add-in root (next to this module). Developers toggle verbose
# logging by creating or deleting that file — no code change is required; the
# flag is evaluated when the add-in loads. The marker file is git-ignored, so it
# never ships in a distribution (where it is absent and DEBUG is therefore False).
DEBUG = os.path.isfile(os.path.join(os.path.dirname(__file__), ".debug"))

# Emit structured [PERF] timing lines from the perf_timer context manager in
# lib/fusionAddInUtils. Zero runtime cost when False. Note that perf lines are
# written through log(), so DEBUG must be on as well.
PERF_TRACE = False

# Attach-debugger gate. When the ``.debug`` marker enables DEBUG (above), the
# add-in also starts an in-process ``debugpy`` server on startup so an external
# DAP client (Zed, or a VS Code "attach" config) can connect. The server is
# non-blocking and localhost-only, and it never runs in a shipped build because
# the ``.debug`` marker is git-ignored and absent there.
WAIT_FOR_DEBUGGER = DEBUG
DEBUGGER_PORT = 5678
# When True, run() blocks until a debugger attaches. Left False so a developer
# who keeps ``.debug`` present for logging is never forced to attach on launch.
DEBUGGER_BLOCK_UNTIL_ATTACHED = False

ADDIN_NAME = os.path.basename(os.path.dirname(__file__))
COMPANY_NAME = "IMA LLC"

design_workspace = "FusionSolidEnvironment"
tools_tab_id = "ToolsTab"
my_tab_name = "Power Tools"
my_panel_id = f"PT_{my_tab_name}"
my_panel_name = "Power Tools"
my_panel_after = ""

CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
INSTALLED_FILE = os.path.join(CACHE_DIR, "installed.json")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
MARKETPLACE_FILE = os.path.join(DATA_DIR, "marketplace.json")


def fusion_addins_dir() -> str:
    """Return the platform-appropriate Fusion AddIns directory path."""
    if platform.system() == "Darwin":
        return os.path.expanduser(
            "~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns"
        )
    return os.path.join(
        os.environ.get("APPDATA", ""),
        "Autodesk", "Autodesk Fusion 360", "API", "AddIns",
    )


def load_installed() -> dict:
    """Return installed add-ins cache, creating it if absent."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    if not os.path.exists(INSTALLED_FILE):
        return {}
    try:
        with open(INSTALLED_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_installed(data: dict) -> None:
    """Persist installed add-ins cache to disk."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(INSTALLED_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_marketplace() -> dict:
    """Return the curated marketplace manifest."""
    with open(MARKETPLACE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
