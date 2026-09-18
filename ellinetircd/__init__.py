# Originally from aioircd
# Copyright (c) 2020 Julien Castiaux
# Original work licensed under the MIT License.
#
# Copyright (c) 2026 ElliNet13
# Modifications licensed under the GNU General Public License v3.0 or later.

import contextvars
import logging
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("ellinetircd")
except PackageNotFoundError:
    __version__ = "unknown"

from ellinetircd.config import config as cfg
logger = logging.getLogger(__package__)
IO = logging.INFO - 5
SECURITY = logging.ERROR + 5
logging.addLevelName(IO, 'IO')
logging.addLevelName(SECURITY, 'SECURITY')
logger.setLevel(cfg.LOGLEVEL)
servlocal = contextvars.ContextVar('servlocal')
MAXLINELEN = 512

import ellinetircd.channel
import ellinetircd.exceptions
import ellinetircd.server
import ellinetircd.sdnotify
import ellinetircd.states
import ellinetircd.user
import ellinetircd.utils
import ellinetircd.shared
import ellinetircd.accounts

ellinetircd.utils.install_templates()

def update_status() -> None:
    sl = servlocal.get()
    ellinetircd.sdnotify.status(
        f"Listening on {cfg.ADDR} ({cfg.HOST}) port {cfg.PORT}. "
        f"Currently {len(sl.users)} registered users"
        f" in {len(sl.channels)} channels."
    )
