# Originally from aioircd
# Copyright (c) 2020 Julien Castiaux
# Original work licensed under the MIT License.
#
# Copyright (c) 2026 ElliNet13
# Modifications licensed under the GNU General Public License v3.0 or later.

import ipaddress
import logging
import re
import trio
import uuid
from typing import List, Optional, Set, Union, TYPE_CHECKING

import ellinetircd
from ellinetircd.config import config as cfg
from ellinetircd.exceptions import IRCException, Disconnect, BotException
from ellinetircd.states import PasswordState, ConnectedState, QuitState, AnyState
import ellinetircd.user

if TYPE_CHECKING:
    from ellinetircd.server import ServLocal

logger = logging.getLogger('ellinetircd.user')

message_re = re.compile(r"""
    (?P<command>[A-Z]+)
    (?P<middle>(?:\ [^\ :]+)*)
    (?:\ :(?P<trailing>.+))?
""", re.VERBOSE)

# Nicknames that users should not use
_unsafe_nicks = {
    # RFC
    'anonymous',
    # anope services
    'ChanServ',
    'NickServ',
    'OperServ',
    'MemoServ',
    'HostServ',
    'BotServ',
}

# Networks allowed to use the above unsafe nicks
_safenets = [
    ipaddress.ip_network('::1/128'),
    ipaddress.ip_network('127.0.0.0/8'),
]


class User:
    def __init__(self, stream: trio.SocketStream, nursery: trio.Nursery) -> None:
        servlocal: "ServLocal" = ellinetircd.servlocal.get()
        self.stream = stream
        self._nursery = nursery
        self._nick: Optional[str] = None
        self._addr = stream.socket.getpeername()
        self._realname: Optional[str] = None
        self.state: AnyState = None
        self.state = (PasswordState if servlocal.pwd else ConnectedState)(self)
        self.channels = set()
        self._ping_timer = trio.CancelScope()  # dummy
        self._send_lock = trio.StrictFIFOLock()

    def __str__(self) -> str:
        if self.nick:
            return self.nick

        ip, port, *_ = self._addr
        if ':' in ip:
            return f'[{ip}]:{port}'
        return f'{ip}:{port}'

    @property
    def nick(self) -> Optional[str]:
        return self._nick
    
    @property
    def addr(self):
        return self._addr
    
    @property
    def host(self) -> str:
        return self._addr[0]
    
    @property
    def realname(self) -> Optional[str]:
        return self._realname

    @nick.setter
    def nick(self, nick: Optional[str]) -> None:
        servlocal = ellinetircd.servlocal.get()
        servlocal.users[nick] = servlocal.users.pop(self._nick, self)
        self._nick = nick

    @realname.setter
    def realname(self, realname: str) -> None:
        self._realname = realname

    def can_use_nick(self, nick: str) -> bool:
        """ Whether this user is allowed to use ``nick``. """
        if nick not in _unsafe_nicks:
            return True

        ip = ipaddress.ip_address(self._addr[0])
        return any(ip in net for net in _safenets)

    async def ping_forever(self) -> None:
        """
        If the user did not send any message for some time, send him a
        PING message that he should answer ASAP with a PONG message. If
        he fails to answer (maybe because the network failed) he'll be
        automatically disconnected, see :meth:`serve`.
        """
        while True:
            with trio.move_on_after(cfg.TIMEOUT - cfg.PING_TIMEOUT) as self._ping_timer:
                await trio.sleep_forever()
            await self.send(f'PING {uuid.uuid4().hex}', log=logger.isEnabledFor(logging.DEBUG))

    async def serve(self) -> None:
        """
        Read for messages on the user socket, parse them and dispatch
        each message to the current's user state.
        """
        buffer = b""
        while type(self.state) is not QuitState:

            # Read the socket in a buffer, wait at most TIMEOUT seconds
            self._ping_timer.deadline = trio.current_time() + (cfg.TIMEOUT - cfg.PING_TIMEOUT)
            with trio.move_on_after(cfg.TIMEOUT) as cs:
                try:
                    chunk = await self.stream.receive_some(ellinetircd.MAXLINELEN)
                except Exception as exc:
                    raise Disconnect("Network failure") from exc
            if cs.cancelled_caught:
                raise Disconnect("Timeout")
            elif not chunk:
                raise Disconnect("End of transmission")

            # Split the buffer into as many IRC messages as possible,
            # ensure each message has a length of maximum MAXLINELEN
            *messages, buffer = (buffer + chunk).split(b'\r\n')
            if any(len(m) > ellinetircd.MAXLINELEN - 2 for m in messages + [buffer]):
                raise Disconnect("Payload too long")

            for message in (m for m in messages if m):
                # IO-log all messages, except PING/PONG that are only
                # log in DEBUG
                if not (message.startswith(b'PING') or message.startswith(b'PONG')
                   ) or logger.isEnabledFor(logging.DEBUG):
                    logger.log(ellinetircd.IO, "recv from %s: %s", self, message)

                # Parse the message
                try:
                    if not (match := message_re.match(message.decode())):
                        raise SyntaxError(f"Couldn't parse {message}")
                except UnicodeDecodeError as exc:
                    raise Disconnect("Gibberish") from exc
                except SyntaxError as exc:
                    raise Disconnect("Parsing error") from exc

                # Re-construct the arguments
                args = [match.group('command')]
                if middle := match.group('middle'):
                    args.extend(middle.split())
                if trailing := match.group('trailing'):
                    args.append(trailing)

                # Execute the command
                if self.state is None:
                    raise ValueError("User state is None")
                
                try:
                    await self.state.dispatch(*args)
                except IRCException as exc:
                    logger.warning("Command %s sent by %s failed, code: %s",
                        args[0], self, exc.code)
                    await self.send(exc.args[0])

    async def terminate(self, kick_msg: str = "Connection terminated by host") -> None:
        """
        Terminate the connection with this user by closing the
        underlying socket and cancelling the user's nursery effectively
        cancelling all user's related tasks.
        """
        logger.info("Terminate connection of %s", self)
        if self.state is None:
            raise ValueError("User state is None")
        if type(self.state) != QuitState:
            await self.state.QUIT(f":{kick_msg}", kick=True)
        with trio.move_on_after(cfg.PING_TIMEOUT) as cs:
            try:
                await self.stream.send_eof()
            except (trio.BrokenResourceError, OSError):
                pass # client already died
        await self.stream.aclose()
        self._nursery.cancel_scope.cancel()

    async def send(
        self,
        messages: Union[str, List[str]],
        log: bool = True,
        skipusers: Optional[Set["ellinetircd.user.User"]] = None,
    ) -> None:
        """ Send many messages to the user. """
        if isinstance(messages, str):
            messages = [messages]

        async with self._send_lock:
            if log:
                for msg in messages:
                    logger.log(ellinetircd.IO, "send to %s: %s", self, msg)
            await self.stream.send_all(b"".join(f"{msg}\r\n".encode() for msg in messages))

class BotUser(User):
    def __init__(self, nursery: trio.Nursery):
        self.servlocal = ellinetircd.servlocal.get()
        server_socket, client_socket = trio.socket.socketpair()
        super().__init__(trio.SocketStream(server_socket), nursery)
        self._client = trio.SocketStream(client_socket)
        self._closed = False
        self._terminated = False
 
    async def __aenter__(self):
        self._nursery.start_soon(self.bot_serve)
        if self.servlocal.pwd is not None:
            await self.usend(f"PASS {self.servlocal.pwd}")
        return self
 
    @property
    def client(self):
        return self._client
 
    @property
    def closed(self):
        return self._closed
 
    @property
    def terminated(self):
        return self._terminated
 
    @property
    def nursery(self):
        return self._nursery
 
    async def usend(self, message: str) -> None:
        """
        Inject a raw IRC line into the server, as if this bot were a
        client typing it. This is the bot's *input* channel -- do not
        confuse it with the inherited `send()`, which is how the
        server delivers output *to* this connection.
        """
        await self._client.send_all(message.rstrip("\r\n").encode("utf-8") + b"\r\n")
 
    async def register(self, nickname: str, realname: str = "EllinetIRCd Local Server Bot") -> None:
        if self.nick is None:
            await self.usend(f"NICK {nickname}")
            await self.usend(f"USER {nickname} 0 * :{realname}")
        else:
            raise BotException("Bot already registered")
 
    async def disconnect(self, reason: str = "Bot is disconnecting") -> None:
        await self.usend(f"QUIT :{reason}")
 
    async def __aexit__(self, exc_type=None, exc=None, tb=None):
        if self._closed:
            return
 
        if not self._terminated:
            await self.disconnect("Bot is done")
 
        self._closed = True
 
    async def bot_serve(self) -> None:
        try:
            await self.serve()
        except Disconnect as exc:
            logger.warning("Protocol violation while serving bot %s, %s.", self.nick, repr(exc.__cause__ or exc))
            await self.terminate(exc.args[0] if exc.args else "Protocol violation")
        except Exception:
            logger.exception("Error while serving bot %s.", self.nick)
            await self.terminate("Internal host error")
        else:
            await self.terminate()
 
    async def terminate(self, kick_msg: str = "Connection terminated by host") -> None:
        self._closed = True
        self._terminated = True
        await super().terminate(kick_msg)
 
    async def join(self, channels: str | list[str], password: Optional[str] = None) -> None:
        channel = ",".join(channels) if isinstance(channels, list) else channels
        await self.usend(f"JOIN {channel}" + (f" {password}" if password else ""))
 
    async def part(self, channels: str | list[str], reason: Optional[str] = None) -> None:
        channel = ",".join(channels) if isinstance(channels, list) else channels
        await self.usend(f"PART {channel}" + (f" :{reason}" if reason else ""))
 
    async def send_message(self, channel: str, message: str) -> None:
        await self.usend(f"PRIVMSG {channel} :{message}")
 