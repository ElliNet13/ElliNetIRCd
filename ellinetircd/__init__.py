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

from . import channel
from . import exceptions
from . import server
from . import sdnotify
from . import states
from . import user
from . import utils
from . import shared
from . import accounts

utils.install_templates()

def update_status() -> None:
    sl = servlocal.get()
    sdnotify.status(
        f"Listening on {cfg.ADDR} ({cfg.HOST}) port {cfg.PORT}. "
        f"Currently {len(sl.users)} registered users"
        f" in {len(sl.channels)} channels."
    )
