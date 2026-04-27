import contextvars
import logging
from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("aioircd")
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


def update_status() -> None:
    sl = servlocal.get()
    ellinetircd.sdnotify.status(
        f"Listening on {cfg.ADDR} ({cfg.HOST}) port {cfg.PORT}. "
        f"Currently {len(sl.users)} registered users"
        f" in {len(sl.channels)} channels."
    )
