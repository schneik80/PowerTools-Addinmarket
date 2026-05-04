# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IMA LLC

from .addinmarket import entry as addinmarket

commands = [
    addinmarket,
]


def start():
    for command in commands:
        command.start()


def stop():
    for command in commands:
        command.stop()
