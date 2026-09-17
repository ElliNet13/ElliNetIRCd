# Originally from aioircd
# Copyright (c) 2020 Julien Castiaux
# Original work licensed under the MIT License.
#
# Copyright (c) 2026 ElliNet13
# Modifications licensed under the GNU General Public License v3.0 or later.

import dataclasses
import logging
import signal
import trio
from typing import Dict, Optional
import tracemalloc

import ellinetircd
from ellinetircd import sdnotify
from ellinetircd.exceptions import Disconnect
from ellinetircd.user import User
from ellinetircd.PluginAPI import GenericContext
from ellinetircd.plugins import GenericPlugin
import ellinetircd.channel
import ellinetircd.plugins

logger = logging.getLogger(__name__)

if logger.isEnabledFor(logging.DEBUG):
    tracemalloc.start()

class Server:
    def __init__(self, host: str, addr: str, port: int, pwd: Optional[str]) -> None:
        self.host = host
        self.addr = addr
        self.port = port
        self.pwd = pwd
        self._plugins = ellinetircd.plugins.find_all_plugins()

    async def handle(self, stream: trio.SocketStream) -> None:
        servlocal = ellinetircd.servlocal.get()
        async with trio.open_nursery() as nursery:
            user = User(stream, nursery)
            logger.info("Connection with %s established.", user)
            nursery.start_soon(user.ping_forever)
            try:
                await user.serve()
            except Disconnect as exc:
                logger.warning("Protocol violation while serving %s, %s.", user, repr(exc.__cause__ or exc))
                await user.terminate(exc.args[0] if exc.args else "Protocol violation")
            except Exception:
                logger.exception("Error while serving %s.", user)
                await user.terminate("Internal host error")
            else:
                await user.terminate()

        logger.info("Connection with %s closed.", user)

    async def _onterm(self) -> None:
        with trio.open_signal_receiver(signal.SIGTERM, signal.SIGINT) as signal_aiter:
            async for _ in signal_aiter:
                if self._nursery.cancel_scope.cancel_called:
                    raise KeyboardInterrupt()
                sdnotify.stopping()
                sdnotify.status("Terminating connections...")
                self._nursery.cancel_scope.cancel()

    async def serve(self) -> None:
        ellinetircd.servlocal.set(ServLocal(self.host, self.pwd, {}, {}, self._plugins))
        async with trio.open_nursery() as self._nursery:
            self._nursery.start_soon(self._onterm)
            logger.info(f"Starting server on {self.addr}:{self.port}...")

            sdnotify.ready()
            ellinetircd.update_status()

            self._nursery.start_soon(self.run_plugins)

            await trio.serve_tcp(self.handle, self.port, host=self.addr)

    async def run_plugins(self) -> None:
        for plugin in self._plugins:
            if isinstance(plugin, GenericPlugin):
                self._nursery.start_soon(plugin.load, GenericContext())


@dataclasses.dataclass(eq=False)
class ServLocal:
    host: str
    pwd: Optional[str]  # password, "pass" is a reserved keyword
    users: Dict[str, User]
    channels: Dict[str, "ellinetircd.channel.Channel"]
    plugins: list[ellinetircd.plugins.PluginBase]

    def __repr__(self) -> str:
        return (
            f'{self.__class__.__name__}('
            f'host: {self.host!r}, '
            f'pass: {"yes" if self.pwd else "no"}, '
            f'users: {len(self.users)}, '
            f'channels: {len(self.channels)}, '
            f'plugins: {len(self.plugins)})'
        )
