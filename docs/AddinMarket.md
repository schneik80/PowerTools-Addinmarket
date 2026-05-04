# Add-in Market

[Back to README](../README.md)

## Overview

The **Add-in Market** command opens a floating palette that serves as a curated in-app marketplace for Autodesk Fusion add-ins. Users can browse, search, and install add-ins from two categories — Core Plugins (officially maintained add-ins) and Community Plugins (contributed by the broader Fusion community) — directly from GitHub without leaving Fusion.

Installed add-ins are registered with Fusion's Scripts API and started immediately. No restart or manual activation is required.

## Prerequisites

- An Autodesk Fusion design document must be open.
- An active internet connection is required to download add-ins.
- Sufficient disk space in `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/` (macOS) or `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\` (Windows).

## Access

The **Add-in Market** command is available in Fusion's **Tools** tab, in the **Power Tools** panel.

1. Open Autodesk Fusion with any document.
2. Select the **Tools** tab in the toolbar.
3. In the **Power Tools** panel, click **Add-in Market**.

## How to Use

### Opening the marketplace

1. Click **Add-in Market** in the Power Tools panel.
2. The marketplace palette opens, defaulting to the **Core Plugins** tab.

### Browsing add-ins

- Each row displays the add-in name, version, publisher, license, and description.
- Switch between **Core Plugins** and **Community Plugins** using the tab buttons at the top.
- Community plugin rows include an **Open on GitHub** link that opens the add-in's readme in your default browser.

### Community add-in notice

When the **Community Plugins** tab is active, a notice appears at the bottom of the palette:

> Community add-ins are third-party software. Review their source code before installing.

Community add-ins are not vetted by IMA LLC. Always review an add-in's source code and readme before installing it.

### Searching and filtering

- Type in the **Search add-ins** field to filter the list by name, description, or publisher. Results update after a short pause.
- Enable the **Installed only** checkbox to show only add-ins currently installed on your machine.

### Installing an add-in

1. Locate the add-in you want to install.
2. Click its toggle switch to turn it **on**.
3. The status bar shows download progress.
4. When complete, the add-in is registered with Fusion and started immediately — its commands and panels are available straight away without restarting Fusion.

> If the add-in cannot be started automatically (for example, it has a malformed manifest), the status bar will prompt you to activate it manually via **Utilities → Add-Ins**.

### Removing an add-in

1. Locate an installed add-in (toggle is **on**).
2. Click its toggle switch to turn it **off**.
3. The add-in is stopped, its files are removed from the AddIns directory, and the cache is updated. No manual intervention is required.

### Version notifications

When the marketplace manifest is updated with a new version of an add-in you have installed, an **⚠ Update available** badge appears on that add-in's row. To update:

1. Toggle the add-in **off** to stop and uninstall the current version.
2. Toggle it **on** to download, install, and start the new version.

No Fusion restart is required — the updated add-in is loaded live in the current session.

## Expected Results

- The **Core Plugins** tab lists all add-ins from the `core` section of `data/marketplace.json`.
- The **Community Plugins** tab lists all add-ins from the `community` section, with a notice reminding users to review third-party code before installing.
- Toggling an add-in on downloads the repository zip, extracts it, places it in the Fusion AddIns directory, and starts it live in the current session.
- The add-in is configured to run on startup automatically for all future Fusion sessions.
- The toggle state persists across palette sessions via `cache/installed.json`.
- The **⚠ Update available** badge appears when the manifest version differs from the installed version.

## Limitations

- **No automatic updates.** Updates must be applied manually (toggle off, then on) to avoid loading conflicts.
- **GitHub branch archives only.** Downloads pull the branch specified by `download_ref` in `marketplace.json`. Add-ins that do not publish a stable branch may not install correctly.
- **No signature verification.** Downloaded zip archives are not cryptographically verified. Only install add-ins from publishers you trust.

---

## Architecture

### System context

```mermaid
C4Context
    title System Context — Add-in Market
    Person(user, "Fusion User", "Designer using Autodesk Fusion")
    System(market, "Add-in Market", "PowerTools add-in that presents a marketplace palette for discovering and installing other Fusion add-ins")
    System_Ext(fusion, "Autodesk Fusion", "Host CAD application")
    System_Ext(github, "GitHub", "Public source for add-in zip archives")
    System_Ext(addins_dir, "Fusion AddIns Directory", "Local filesystem directory scanned by Fusion at startup")

    Rel(user, market, "Opens palette, toggles add-ins")
    Rel(market, fusion, "Registers command, sends theme, shows palette, loads/stops add-ins via Scripts API")
    Rel(market, github, "Downloads zip archive via HTTPS")
    Rel(market, addins_dir, "Extracts and installs add-in files")
    Rel(fusion, addins_dir, "Scans on startup to load add-ins not yet registered this session")
```

### Container diagram

```mermaid
C4Container
    title Container Diagram — Add-in Market
    Person(user, "Fusion User")

    Container_Boundary(addin, "PowerTools-Addinmarket") {
        Container(entry, "entry.py", "Python", "Command lifecycle, palette management, JSON-RPC dispatcher")
        Container(installer, "installer.py", "Python", "Downloads zip, extracts, moves to AddIns dir, registers and starts via Scripts API, updates cache")
        Container(config, "config.py", "Python", "Paths, helpers for marketplace manifest and installed cache")
        Container(html, "marketplace.html + .js", "HTML / JavaScript", "Palette UI: tabs, search, toggle switches, community notice, RPC client")
        Container(css, "marketplace.css", "CSS", "Fusion-themed dark/light styles; dark default with explicit html[data-theme] override")
        ContainerDb(manifest, "data/marketplace.json", "JSON", "Curated add-in list: name, description, publisher, license, repo")
        ContainerDb(cache, "cache/installed.json", "JSON", "Installed add-in versions and paths (not committed)")
    }

    System_Ext(fusion, "Autodesk Fusion")
    System_Ext(github, "GitHub")

    Rel(user, html, "Interacts with palette UI")
    Rel(html, entry, "JSON-RPC via adsk.fusionSendData / sendInfoToHTML")
    Rel(entry, installer, "Calls install() / uninstall()")
    Rel(entry, config, "Reads marketplace manifest and installed cache")
    Rel(installer, github, "Downloads zip via urllib.request")
    Rel(installer, fusion, "app.scripts.addExisting() / script.run() / script.stop()")
    Rel(installer, cache, "Reads and writes installed.json")
    Rel(config, manifest, "Reads marketplace.json")
    Rel(entry, fusion, "Registers command, manages palette")
```

### Component diagram

```mermaid
C4Component
    title Component Diagram — Add-in Market Command
    Container_Boundary(entry_py, "entry.py") {
        Component(start, "start()", "Python", "Registers command definition and toolbar button")
        Component(stop, "stop()", "Python", "Removes button and palette on add-in stop")
        Component(cmd_exec, "command_execute()", "Python", "Creates or re-shows the palette; detects and pushes theme")
        Component(rpc_disp, "palette_incoming()", "Python", "Dispatches incoming RPC envelopes to handler functions")
        Component(rpc_list, "_rpc_list_addins()", "Python", "Merges marketplace.json with installed.json to produce row data")
        Component(rpc_inst, "_rpc_install()", "Python", "Looks up entry in manifest and calls installer.install()")
        Component(rpc_uninst, "_rpc_uninstall()", "Python", "Calls installer.uninstall()")
        Component(rpc_readme, "_rpc_open_readme()", "Python", "Opens GitHub URL in system browser via subprocess")
        Component(reply, "_reply()", "Python", "Sends JSON-RPC reply back to HTML via sendInfoToHTML")
    }
    Container_Boundary(inst_py, "installer.py") {
        Component(install_fn, "install()", "Python", "Download + extract + move + load via API + update cache")
        Component(uninstall_fn, "uninstall()", "Python", "Stop via API + remove directory + update cache")
        Component(load_fn, "_load_addin()", "Python", "app.scripts.addExisting() → script.run(); sets isRunOnStartup")
        Component(stop_fn, "_stop_addin()", "Python", "app.scripts.itemByPath() → script.stop() → script.unlink()")
    }

    Rel(rpc_disp, rpc_list, "method=listAddins")
    Rel(rpc_disp, rpc_inst, "method=install")
    Rel(rpc_disp, rpc_uninst, "method=uninstall")
    Rel(rpc_disp, rpc_readme, "method=openReadme")
    Rel(rpc_inst, install_fn, "calls")
    Rel(rpc_uninst, uninstall_fn, "calls")
    Rel(install_fn, load_fn, "calls after files are in place")
    Rel(uninstall_fn, stop_fn, "calls before deleting files")
    Rel(rpc_list, reply, "→ result list")
    Rel(rpc_inst, reply, "→ ok / error")
    Rel(rpc_uninst, reply, "→ ok / error")
```

### Install sequence

```mermaid
sequenceDiagram
    actor User
    participant JS as marketplace.js
    participant Py as entry.py
    participant Inst as installer.py
    participant GH as GitHub
    participant FS as AddIns Directory
    participant API as Fusion Scripts API

    User->>JS: Toggle add-in ON
    JS->>Py: RPC install { id, tab }
    Py->>Py: Look up entry in marketplace.json
    Py->>Inst: install(entry)
    Inst->>GH: GET /archive/refs/heads/ref.zip
    GH-->>Inst: zip stream
    Inst->>FS: Extract and move folder to AddIns/id
    Inst->>API: scripts.addExisting(dest_path)
    API-->>Inst: Script object
    Inst->>API: script.isRunOnStartup = True
    Inst->>API: script.run()
    Inst->>Inst: Update cache/installed.json
    Inst-->>Py: { ok: True, message }
    Py->>JS: rpcReply { ok, result.message }
    JS->>User: Status bar: "Installed and started"
```

### Update notification workflow

```mermaid
flowchart TD
    A[Palette opens] --> B[listAddins RPC]
    B --> C[Load marketplace.json]
    B --> D[Load installed.json]
    C --> E{For each add-in}
    D --> E
    E --> F{Is installed?}
    F -- No --> G[installed: false]
    F -- Yes --> H{manifest version == installed version?}
    H -- Yes --> I[installed: true, update_available: false]
    H -- No --> J[installed: true, update_available: true]
    G --> K[Render row: toggle OFF]
    I --> L[Render row: toggle ON]
    J --> M[Render row: toggle ON + ⚠ badge]
```

---

[Back to README](../README.md)

*Copyright © 2026 IMA LLC. All rights reserved.*
