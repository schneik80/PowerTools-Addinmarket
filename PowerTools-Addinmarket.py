# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IMA LLC

from . import config
from . import commands
from .lib import fusionAddInUtils as futil


def run(context):
    try:
        if config.WAIT_FOR_DEBUGGER:
            import debugpy
            if not getattr(debugpy, "_fusion_listening", False):
                try:
                    debugpy.listen(
                        ("127.0.0.1", config.DEBUGGER_PORT),
                        in_process_debug_adapter=True,
                    )
                except RuntimeError:
                    pass
                debugpy._fusion_listening = True
            if config.DEBUGGER_BLOCK_UNTIL_ATTACHED:
                debugpy.wait_for_client()

        commands.start()
    except:
        futil.handle_error('run')


def stop(context):
    try:
        futil.clear_handlers()
        commands.stop()
    except:
        futil.handle_error('stop')
