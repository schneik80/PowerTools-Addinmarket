# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IMA LLC
"""
Download, extract, and remove Fusion add-ins from GitHub.

Install flow:
  1. Build archive URL from the entry's github_repo + download_ref.
  2. Stream the zip to a temp file via urllib.request.
  3. Extract to a temp directory, identify the top-level folder.
  4. Move (or replace) it into the Fusion AddIns directory under the add-in id.
  5. Register it with Fusion via app.scripts.addExisting() and call run() so
     the add-in is live immediately — no restart required.
  6. Set isRunOnStartup = True so it loads automatically in future sessions.
  7. Record the installed version and path in cache/installed.json.

Uninstall flow:
  1. Look up the path in cache/installed.json.
  2. Stop the running add-in via app.scripts.itemByPath().stop().
  3. Unlink it from Fusion's known scripts list if it was linked.
  4. Remove the directory tree.
  5. Remove the entry from the cache.
"""

import datetime
import os
import shutil
import tempfile
import urllib.request
import zipfile

import adsk.core

from ... import config
from ...lib import fusionAddInUtils as futil


def install(entry: dict) -> dict:
    """
    Download and install the add-in described by *entry*.

    Parameters
    ----------
    entry : dict
        A single record from data/marketplace.json. Must contain at minimum
        ``id``, ``github_repo``, ``download_ref``, and ``version``.

    Returns
    -------
    dict
        ``{ "ok": True, "message": "..." }`` on success, raises on failure.
    """
    addin_id = entry["id"]
    repo = entry["github_repo"]
    ref = entry.get("download_ref", "main")
    version = entry.get("version", "unknown")

    download_url = f"https://github.com/{repo}/archive/refs/heads/{ref}.zip"
    futil.log(f"Installer: downloading {addin_id} from {download_url}")

    addins_dir = config.fusion_addins_dir()
    os.makedirs(addins_dir, exist_ok=True)

    dest_path = os.path.join(addins_dir, addin_id)

    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_path = os.path.join(tmp_dir, f"{addin_id}.zip")

        # Download
        urllib.request.urlretrieve(download_url, zip_path)
        futil.log(f"Installer: downloaded to {zip_path}")

        # Extract
        extract_dir = os.path.join(tmp_dir, "extracted")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)

        # GitHub zips contain a single top-level folder named <repo>-<ref>
        entries = os.listdir(extract_dir)
        if len(entries) != 1:
            raise RuntimeError(
                f"Expected one top-level folder in zip, found: {entries}"
            )
        extracted_root = os.path.join(extract_dir, entries[0])

        # Replace existing installation if present
        if os.path.exists(dest_path):
            shutil.rmtree(dest_path)
        shutil.move(extracted_root, dest_path)
        futil.log(f"Installer: installed to {dest_path}")

    # Register with Fusion and start immediately
    loaded = _load_addin(dest_path, addin_id)

    # Update installed cache
    installed = config.load_installed()
    installed[addin_id] = {
        "version": version,
        "installed_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "path": dest_path,
    }
    config.save_installed(installed)

    name = entry.get("name", addin_id)
    if loaded:
        message = f'"{name}" installed and started successfully.'
    else:
        message = f'"{name}" installed. Restart Fusion or use Utilities → Add-Ins to activate it.'

    return {"ok": True, "message": message}


def uninstall(addin_id: str) -> dict:
    """
    Remove an installed add-in by id.

    Parameters
    ----------
    addin_id : str
        The add-in id as recorded in cache/installed.json.

    Returns
    -------
    dict
        ``{ "ok": True }`` on success, raises on failure.
    """
    installed = config.load_installed()
    entry = installed.get(addin_id)
    if not entry:
        raise ValueError(f"'{addin_id}' is not recorded as installed")

    path = entry.get("path", "")

    # Stop and unregister from the running session before deleting files
    _stop_addin(path)

    if path and os.path.exists(path):
        shutil.rmtree(path)
        futil.log(f"Installer: removed {path}")
    else:
        futil.log(f"Installer: path not found, removing from cache only: {path}")

    del installed[addin_id]
    config.save_installed(installed)

    return {"ok": True}


# ---------------------------------------------------------------------------
# Fusion session helpers
# ---------------------------------------------------------------------------

def _load_addin(dest_path: str, addin_id: str) -> bool:
    """Register and start the add-in in the current Fusion session.

    Returns True if the add-in was successfully started, False if it needs
    a manual restart (e.g. missing manifest, API error).
    """
    try:
        scripts = adsk.core.Application.get().scripts

        # Reuse existing Script object if Fusion already knows this path
        script = scripts.itemByPath(dest_path)
        if script is None:
            script = scripts.addExisting(dest_path)
        if script is None:
            futil.log(f"Installer: addExisting returned None for {addin_id}")
            return False

        script.isRunOnStartup = True
        if not script.isRunning:
            script.run()

        futil.log(f"Installer: started {addin_id}")
        return True

    except Exception as exc:
        futil.log(f"Installer: could not start {addin_id} via API: {exc}")
        return False


def _stop_addin(dest_path: str) -> None:
    """Stop and unlink the add-in from the current Fusion session."""
    if not dest_path:
        return
    try:
        scripts = adsk.core.Application.get().scripts
        script = scripts.itemByPath(dest_path)
        if script is None:
            return

        if script.isRunning:
            script.stop()
            futil.log(f"Installer: stopped add-in at {dest_path}")

        # unlink() is only valid for linked (non-standard-location) add-ins
        try:
            script.unlink()
        except Exception:
            pass

    except Exception as exc:
        futil.log(f"Installer: could not stop add-in at {dest_path}: {exc}")
