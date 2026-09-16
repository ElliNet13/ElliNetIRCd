# Originally from aioircd
# Copyright (c) 2020 Julien Castiaux
# Original work licensed under the MIT License.
#
# Copyright (c) 2026 ElliNet13
# Modifications licensed under the GNU General Public License v3.0 or later.

import logging
import os
from socket import gethostname, gethostbyname
from types import SimpleNamespace


config = SimpleNamespace()
config.HOST = os.getenv('HOST', gethostname())
config.ADDR = os.getenv('ADDR', gethostbyname(config.HOST))
config.PORT = int(os.getenv('PORT', 6667))
config.PASS = os.getenv('PASS')
config.TIMEOUT = int(os.getenv('TIMEOUT', 60))
config.PING_TIMEOUT = int(os.getenv('PING_TIMEOUT', 5))
config.LOGLEVEL = os.getenv('LOGLEVEL', 'WARNING')
