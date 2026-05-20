# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IMA LLC

import os
import json
import platform
from .lib import fusionAddInUtils as futil

DEBUG = True

# When True, start a debugpy server on startup so Zed (or any DAP client) can attach.
# Leave False for shipping builds.
WAIT_FOR_DEBUGGER = False
DEBUGGER_PORT = 5678
DEBUGGER_BLOCK_UNTIL_ATTACHED = False  # set True to pause run() until Zed attaches

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
