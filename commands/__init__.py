# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IMA LLC

from .addinmarket import entry as addinmarket

from ..lib import fusionAddInUtils as futil

commands = [
    addinmarket,
]


def start():
    for command in commands:
        try:
            command.start()
        except Exception:
            futil.handle_error(command.__name__)


def stop():
    for command in commands:
        try:
            command.stop()
        except Exception:
            futil.handle_error(command.__name__)
