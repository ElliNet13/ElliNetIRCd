__all__ = [
    'UserState', 'ConnectedState', 'PasswordState', 'RegisteredState',
    'QuitState'
]

import abc
import inspect
import ipaddress
import logging
import re
import textwrap
import trio
from typing import Any, Callable, Dict, List, Optional, Set, TypeVar

import ellinetircd
from ellinetircd.channel import Channel
from ellinetircd.exceptions import *

FuncType = TypeVar('FuncType', bound=Callable[..., Any])


logger = logging.getLogger(__name__)
nick_re = re.compile(r"[a-zA-Z][a-zA-Z0-9\-_]{1,15}")
chan_re = re.compile(r"[&#][a-zA-Z0-9\-_]{1,49}")


def command(func: FuncType) -> FuncType:
    """ Denote the function can be triggered by an IRC message """
    func.command = True
    return func


class UserState(metaclass=abc.ABCMeta):
    def __init__(self, user: "ellinetircd.user.User") -> None:
        logger.debug("state of user %s changed: %s -> %s", user, user.state, self)
        self.user = user

    def __str__(self) -> str:
        return type(self).__name__[:-5]

    async def dispatch(self, cmd: str, *params: str) -> None:
        logger.debug('Dispatch to %s: %s', cmd, params)
        meth = getattr(self, cmd, None)
        if not meth or not getattr(meth, 'command', False):
            raise ErrUnknownError(self.user, '-', f"Command {cmd} is unknown.")

        sign = inspect.signature(meth)
        try:
            sign.bind(*params)
        except TypeError:
            meth_params_cnt = len(inspect.signature(meth).parameters.values())
            if len(params) < meth_params_cnt:
                raise ErrNeedMoreParams(cmd)
            else:
                raise ErrUnknownError(self.user, cmd, f"Couldn't bind {params} to {sign}.")

        await meth(*params)

    @command
    async def PING(self, token: str) -> None:
        host = ellinetircd.servlocal.get().host
        await self.user.send(f":{host} PONG {host} {token}", log=logger.isEnabledFor(logging.DEBUG))

    @command
    async def PONG(self, token: Optional[str] = None) -> None:
        pass  # ignored


    @command
    async def USER(self, username: str, _zero: str, _star: str, realname: str) -> None:
        raise ErrUnknownError(self.user, "USER", "Called while in the wrong state.")

    @command
    async def PASS(self, password: str) -> None:
        raise ErrUnknownError(self.user, "PASS", "Called while in the wrong state.")

    @command
    async def NICK(self, nickname: str) -> None:
        raise ErrUnknownError(self.user, "NICK", "Called while in the wrong state.")
    
    @command
    async def WHO(self, channel: str) -> None:
        raise ErrUnknownError(self.user, "WHO", "Called while in the wrong state.")
    
    @command
    async def WHOIS(self, channel: str) -> None:
        raise ErrUnknownError(self.user, "WHOIS", "Called while in the wrong state.")

    @command
    async def JOIN(self, channels: str) -> None:
        raise ErrUnknownError(self.user, "JOIN", "Called while in the wrong state.")

    @command
    async def PART(self, channels: str, reason: Optional[str] = None) -> None:
        raise ErrUnknownError(self.user, "PART", "Called while in the wrong state.")

    @command
    async def NAMES(self, channel: str) -> None:
        raise ErrUnknownError(self.user, "NAMES", "Called while in the wrong state.")

    @command
    async def LIST(self) -> None:
        raise ErrUnknownError(self.user, "LIST", "Called while in the wrong state.")

    @command
    async def PRIVMSG(self, args: str) -> None:
        raise ErrUnknownError(self.user, "PRIVMSG", "Called while in the wrong state.")
    
    @command
    async def MODE(self, args: str) -> None:
        raise ErrUnknownError(self.user, "MODE", "Called while in the wrong state.")

    @command
    async def QUIT(self, reason: str = "", *, kick: bool = False) -> None:
        servlocal = ellinetircd.servlocal.get()
        if not kick:
            reason = 'Quit: ' + reason
        for chan in self.user.channels:
            chan.users.remove(self.user)
            await chan.send(f":{self.user.nick} QUIT :{reason}")
            if not chan.users:
                servlocal.channels.pop(chan.name)
        self.user.channels.clear()
        self.user.state = QuitState(self.user)


class PasswordState(UserState):
    @command
    async def PASS(self, password: str) -> None:
        servlocal = ellinetircd.servlocal.get()
        if password != servlocal.pwd:
            logger.log(ellinetircd.SECURITY, "Invalid password for %s", self.user)
            raise ErrPasswdMismatch()

        self.user.state = ConnectedState(self.user)


class ConnectedState(UserState):
    """
    The user is just connected, he must register via the NICK command
    first before going on.
    """
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.has_nick = False
        self.has_user = False
        self.cap_ended = False
        self.cap_started = False

    @command
    async def CAP(self, subcommand: str, *params: str) -> None:
        host = ellinetircd.servlocal.get().host
        subcommand = subcommand.upper()
        self.cap_started = True

        CAPS = [
            "away-notify",
            "cap-notify",
            "multi-prefix",
            "chghost",
        ]
        caps = " ".join(CAPS)

        if subcommand == 'LS':
            await self.user.send(f":{host} CAP * LS :{caps}")
        elif subcommand == 'LIST':
            await self.user.send(f":{host} CAP * LIST :{caps}")
        elif subcommand == 'REQ':
            requested = set(params[-1].split())

            supported = CAPS
            unknown = requested.difference(supported)

            if unknown:
                await self.user.send(
                    f":{host} CAP * NAK :{' '.join(unknown)}"
                )
            else:
                await self.user.send(
                    f":{host} CAP * ACK :{' '.join(requested)}"
                )
        elif subcommand == 'END':
            self.cap_ended = True
            if self.has_user and self.has_nick:
                await self.register()
        else:
            raise ErrUnknownError(self.user, "CAP", f"Unknown CAP subcommand {subcommand}.")

    @command
    async def PASS(self, password: str) -> None:
        raise ErrAlreadyRegistred()

    @command
    async def USER(self, username: str, _zero: str, _star: str, realname: str) -> None:
        self.has_user = True
        self.user.realname = realname
        if self.has_user and self.has_nick and (not self.cap_started or self.cap_ended):
            await self.register()

    @command
    async def NICK(self, nickname: str) -> None:
        servlocal = ellinetircd.servlocal.get()
        if nickname in servlocal.users:
            raise ErrNicknameInUse(nickname)
        if not nick_re.match(nickname):
            raise ErrErroneusNickname(nickname)
        if not self.user.can_use_nick(nickname):
            logger.log(ellinetircd.SECURITY, '%s tried to use nick %s', self.user, nickname)
            raise ErrErroneusNickname(nickname)

        self.user.nick = nickname
        self.has_nick = True
        if self.has_user and self.has_nick and (not self.cap_started or self.cap_ended):
            await self.register()

    async def register(self) -> None:
        servlocal = ellinetircd.servlocal.get()
        self.user.state = RegisteredState(self.user)
        ellinetircd.update_status()
        await self.user.send(textwrap.dedent("""\
            :{host} 001 {nick} :Welcome to the Internet Relay Network {nick}
            :{host} 002 {nick} :Your host is {host}, running version {version}
            :{host} 003 {nick} :The server was created someday
            :{host} 004 {nick} ellinetircd {version} {usermodes} {chanmodes}
            :{host} 005 {nick} {cap1} :are supported by this server
            :{host} 005 {nick} {cap2} :are supported by this server
            :{host} 422 {nick} :MOTD File is missing""".format(
                host=servlocal.host,
                nick=self.user.nick,
                version=ellinetircd.__version__,
                # RPL_MYINFO (004), advertise availables modes (none)
                usermodes="",
                chanmodes="",
                # RPL_ISUPPORT (005), advertise server capabilities (not much)
                cap1 = "AWAYLEN=0 CASEMAPPING=ascii CHANLIMIT=#: CHANMODES= CHANNELLEN=50 CHANTYPES=# ELIST=",
                cap2 = "HOSTLEN=63 KICKLEN=0 MAXLIST= MAXTARGETS=12 MODES=0 NICKLEN=15 STATUSMSG= TOPICLEN=0 USERLEN=15",
            )
        ).split('\n'))

class RegisteredState(UserState):
    """
    The user sent the NICK command, he is fully registered to the server
    and may use any command.
    """

    @command
    async def PASS(self, password: str) -> None:
        raise ErrAlreadyRegistred()

    @command
    async def USER(self, username: str, _zero: str, _star: str, realname: str) -> None:
        raise ErrAlreadyRegistred()

    @command
    async def NICK(self, nickname: str) -> None:
        servlocal = ellinetircd.servlocal.get()

        if nickname in servlocal.users:
            raise ErrNicknameInUse(nickname)
        if not nick_re.match(nickname):
            raise ErrErroneusNickname(nickname)

        old_nick = self.user.nick
        async with trio.open_nursery() as nursery:
            for chan in self.user.channels:
                nursery.start_soon(chan.send, f":{old_nick} NICK {nickname}")

        self.user.nick = nickname

    @command
    async def JOIN(self, channels: str) -> None:
        servlocal = ellinetircd.servlocal.get()

        for channel in channels.split(','):
            if not chan_re.match(channel):
                await self.user.send(ErrNoSuchChannel.format(channel))
                continue

            # Find or create the channel, add the user in it
            chan = servlocal.channels.get(channel)
            if not chan:
                chan = Channel(channel)
                servlocal.channels[chan.name] = chan
                ellinetircd.update_status()
            chan.users.add(self.user)
            self.user.channels.add(chan)

            # Send JOIN response to all
            await chan.send(f":{self.user.nick} JOIN {channel}")

            # Send NAMES list to joiner
            await self.NAMES(channel)

    @command
    async def PART(self, channels: str, reason: Optional[str] = None) -> None:
        servlocal = ellinetircd.servlocal.get()

        for channel in channels.split(','):
            chan = servlocal.channels.get(channel)
            if not chan:
                await self.user.send(ErrNoSuchChannel.format(channel))
                continue

            if self.user not in chan.users:
                await self.user.send(ErrNotOnChannel.format(channel))
                continue

            self.user.channels.remove(chan)
            chan.users.remove(self.user)
            if not chan.users:
                servlocal.channels.pop(chan.name)
                ellinetircd.update_status()

            if reason:
                await chan.send(f":{self.user.nick} PART {channel} :{reason}")
            else:
                await chan.send(f":{self.user.nick} PART {channel}")

    @command
    async def NAMES(self, channel: str) -> None:
        servlocal = ellinetircd.servlocal.get()
        chan = servlocal.channels.get(channel)
        host = servlocal.host
        nick = self.user.nick

        if chan:
            await self.user.send([
                f":{host} 353 {nick} = {chan} :{some_users}"
                # merged all users in a str and split it by MAXLINELEN chunks
                for some_users in textwrap.wrap(
                    ' '.join(sorted(user.nick for user in chan.users)),
                    width=ellinetircd.MAXLINELEN - len(host) - len(nick) - len(channel) - 13
                )
            ])

        await self.user.send(f":{host} 366 {nick} {chan} :End of /NAMES list.")
            
    @command
    async def LIST(self) -> None:
        servlocal = ellinetircd.servlocal.get()
        host = servlocal.host
        nick = self.user.nick

        await self.user.send([
            f":{host} 321 {nick} Channel :Users Name",
            *[
                f":{host} 322 {nick} {chan} {len(chan.users)} :"
                for chan in servlocal.channels.values()
            ],
            f":{host} 323 {nick} :End of /LIST"
        ])

    @command
    async def PRIVMSG(self, targets: str, text: str) -> None:
        servlocal = ellinetircd.servlocal.get()

        for target in targets.split(','):
            chan_or_user = (
                servlocal.channels.get(target)
                if target.startswith(('&', '#')) else
                servlocal.users.get(target)
            )

            if not chan_or_user:
                await self.user.send(ErrNoSuchNick.format(target))
                continue

            await chan_or_user.send(
                f":{self.user.nick} PRIVMSG {target} :{text}",
                skipusers={self.user}
            )

    @command
    async def WHO(self, target: str = "*") -> None:
        servlocal = ellinetircd.servlocal.get()
        host = servlocal.host
        requester = self.user.nick
    
        def match(user: "ellinetircd.user.User", target: str) -> bool:
            if target == "*" or target == "":
                return True
            if target.startswith("#"):
                return user in servlocal.channels.get(target, set()).users
            return target.lower() in user.nick.lower()
    
        users = set()
    
        # Channel WHO
        if target.startswith("#"):
            chan = servlocal.channels.get(target)
            if chan:
                users = chan.users
    
        # Global / nick WHO
        else:
            for chan in servlocal.channels.values():
                users.update(chan.users)
    
            users = [u for u in users if target == "*" or target.lower() in u.nick.lower()]
    
        # Send WHO replies
        for user in users:
            await self.user.send(
                f":{host} 352 {requester} "
                f"{target} "
                f"~{user.nick} "
                f"{user.host} "
                f"{host} "
                f"{user.nick} "
                f"H :0 {user.realname}"
            )
    
        # End of WHO list
        await self.user.send(
            f":{host} 315 {requester} {target} :End of /WHO list."
        )

    @command
    async def WHOIS(self, target: str) -> None:
        servlocal = ellinetircd.servlocal.get()
        host = servlocal.host
        requester = self.user.nick

        user = servlocal.users.get(target)
        if not user:
            raise ErrNoSuchNick(target)

        await self.user.send(
            f":{host} 311 {requester} {target} ~{user.nick} {user.host} {host} :{user.realname}"
        )
        await self.user.send(
            f":{host} 312 {requester} {target} {host} :ellinetircd"
        )

        channels = ' '.join(sorted(chan.name for chan in user.channels))
        if channels:
            await self.user.send(
                f":{host} 319 {requester} {target} :{channels}"
            )

        await self.user.send(
            f":{host} 318 {requester} {target} :End of /WHOIS list."
        )

    @command
    async def MODE(self, target: Optional[str] = None, *params: str) -> None:
        servlocal = ellinetircd.servlocal.get()
        host = servlocal.host
        nick = self.user.nick

        # Replace IF I add a MODE system

        # User MODE query
        if not target or target == self.user.nick:
            await self.user.send(
                f":{host} 221 {nick} +"
            )
            return

        # Channel MODE query
        if target.startswith("#") or target.startswith("&"):
            if target not in servlocal.channels:
                await self.user.send(ErrNoSuchChannel.format(target))
                return

            # Placeholder: pretend all channels are "+nt"
            await self.user.send(
                f":{host} 324 {nick} {target} +nt"
            )
            await self.user.send(
                f":{host} 329 {nick} {target} 0"
            )
            return

        # Unknown target (nick etc.)
        await self.user.send(
            ErrNoSuchNick.format(target)
        )

class QuitState(UserState):
    """ The user sent the QUIT command, no more message should be processed """
    def __init__(self, user: "ellinetircd.user.User") -> None:
        super().__init__(user)
        user.nick = None
        ellinetircd.update_status()

    @command
    async def PING(self, server1: Optional[str] = None, server2: Optional[str] = None) -> None:
        raise ErrUnknownError(self.user, "PING", "Called while in the wrong state.")

    @command
    async def PONG(self, server1: Optional[str] = None, server2: Optional[str] = None) -> None:
        raise ErrUnknownError(self.user, "PONG", "Called while in the wrong state.")

    @command
    def QUIT(self, args: str) -> None:
        raise ErrUnknownError(self.user, "QUIT", "Called while in the wrong state.")
