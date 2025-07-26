#!/usr/bin/env python3
"""
Traktarr - Main Entry Point

This is the main entry point for Traktarr that imports and runs the CLI commands.
"""

import signal
from pyfiglet import Figlet

from cli.commands import app
from core.business_logic import exit_handler


if __name__ == "__main__":
    print("")

    f = Figlet(font='graffiti')
    print(f.renderText('Traktarr'))

    print("""
#########################################################################
# Author:   ShadyBoukhary                                              #
# URL:      https://github.com/ShadyBoukhary/traktarr                   #
# --                                                                    #
#         Part of the Cloudbox project: https://cloudbox.works          #
#########################################################################
#                   GNU General Public License v3.0                     #
#########################################################################
""")

    # Register the signal handlers
    signal.signal(signal.SIGTERM, exit_handler)
    signal.signal(signal.SIGINT, exit_handler)

    # Start application
    app()
