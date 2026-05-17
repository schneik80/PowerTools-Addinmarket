# PowerTools: Add-in Market for Autodesk Fusion

Add-in Market is an Autodesk Fusion add-in that provides a curated in-app marketplace for discovering and installing other Fusion add-ins. It presents a searchable, filterable list of add-ins sourced from a local manifest, with toggle switches to download and install each add-in directly from GitHub.

## Prerequisites

Before you install and run this add-in, confirm that you have the following:

- **Autodesk Fusion** (any current subscription tier) with Python add-in support enabled
- **Windows 10/11** or **macOS**
- An active internet connection (required for downloading add-ins)

## Installation

1. Download or clone this repository to your local machine.
2. In Autodesk Fusion, open the **Add-Ins** dialog by selecting **Utilities** > **Add-Ins**, or press **Shift+S**.
3. On the **Add-Ins** tab, click the green **+** icon.
4. Navigate to the folder where you placed the add-in files and select the `PowerTools-Addinmarket` folder.
5. Click **Open**.
6. Select **Add-in Market** in the list, then click **Run**.

To have the add-in load automatically each time Fusion starts, select **Run on Startup** before clicking **Run**.

## Commands

| Command | Location | Description |
| --- | --- | --- |
| [Add-in Market](./docs/AddinMarket.md) | Tools &rsaquo; Power Tools | Browse and install Fusion add-ins from the PowerTools curated marketplace. |

---

## Add-in Market

The **Add-in Market** command opens a floating palette that lists curated Fusion add-ins in two categories.

### Core Plugins

Officially maintained add-ins from IMA LLC. Each row shows the add-in name, version, publisher, license, and description, with a toggle switch to install or remove it.

### Community Plugins

Third-party add-ins contributed by the broader Fusion community. Each row includes all core fields plus a link to open the add-in's GitHub readme in your default browser.

### Filtering and search

- Type in the search box to filter by name, description, or publisher.
- Enable **Installed only** to see only add-ins currently installed on your machine.

### Version notifications

When a new version of a previously installed add-in is released and the marketplace manifest is updated, an **⚠ Update available** badge appears on the add-in's row. Toggle the add-in off to stop and remove the current version, then toggle it on to download, install, and start the new version — no Fusion restart required.

For full usage details, see [Add-in Market](./docs/AddinMarket.md).

---

## Support

This add-in is developed and maintained by IMA LLC.

---

## License

This project is released under the [GNU General Public License v3.0 or later](LICENSE).

Copyright (C) 2026 IMA LLC.

The shared library at `lib/fusionAddInUtils` is vendored byte-for-byte identically across all nine PowerTools add-ins. It mixes code under different terms: `general_utils.py`, `event_utils.py`, and `attributes_utils.py` are based on Autodesk, Inc. sample code (distributed under its own license terms — see the source headers); `cache_utils.py`, `date_utils.py`, `log_utils.py`, and `upload_utils.py` are part of this project (IMA LLC, GPL-3.0-or-later). See each module's source header for details.

---

*Copyright © 2026 IMA LLC. All rights reserved.*
