# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IMA LLC

from . import commands
from .lib import fusionAddInUtils as futil


def run(context):
    try:
        commands.start()
    except:
        futil.handle_error('run')


def stop(context):
    try:
        futil.clear_handlers()
        commands.stop()
    except:
        futil.handle_error('stop')
