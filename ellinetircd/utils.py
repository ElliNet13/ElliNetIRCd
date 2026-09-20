# Copyright (c) 2026 ElliNet13
# Licensed under the GNU General Public License v3.0 or later.

from importlib.resources import files
from pathlib import Path
import shutil
import os
import signal

from typing import TYPE_CHECKING, Optional

import ellinetircd

if TYPE_CHECKING:
    from ellinetircd.user import User
    from ellinetircd.server import ServLocal

async def send_system_message(user: "User", messages: str|list[str], error: bool = False, custom_numeric: Optional[int] = None) -> None:
    servlocal: "ServLocal" = ellinetircd.servlocal.get()

    message_type = (
        custom_numeric if custom_numeric is not None else "400"
    ) if error else "NOTICE"

    if type(messages) == str:
        messages_new = [messages]

    for i, message in enumerate(messages_new):
        messages_new[i] = f":{servlocal.host} {message_type} {user.nick} :{message}"

    await user.send(messages_new)

def install_template(name: str, destination: Path) -> None:
    template = files("ellinetircd").joinpath("templates", name)

    destination.parent.mkdir(parents=True, exist_ok=True)

    if not destination.exists():
        with template.open("rb") as source:
            with destination.open("wb") as target:
                shutil.copyfileobj(source, target)

def install_templates(destination: Path = Path(".").resolve()) -> None:
    """Install all bundled YAML templates into the destination directory."""
    templates = files("ellinetircd").joinpath("templates")

    destination.mkdir(parents=True, exist_ok=True)

    for template in templates.iterdir():
        if not template.is_file() or template.name.endswith((".yaml", ".yml")) is False:
            continue

        target = destination / template.name

        if target.exists():
            continue

        with template.open("rb") as source, target.open("wb") as output:
            shutil.copyfileobj(source, output)

def find_user_from_nick(nick: str) -> Optional["User"]:
    servlocal: "ServLocal" = ellinetircd.servlocal.get()

    for user in servlocal.users.values():
        if user.nick == nick:
            return user
    return None

async def shutdown() -> None:
    """Shut down the server."""
    servlocal: "ServLocal" = ellinetircd.servlocal.get()
    for user in servlocal.users.values():
        await send_system_message(user, "Server is shutting down", error=True)
    os.kill(os.getpid(), signal.SIGINT)
    return

class Fuse:
    def __init__(self) -> None:
        self.__blown = False

    def __bool__(self) -> bool:
        return not self.__blown

    def __call__(self) -> bool:
        is_blown = self.__blown
        self.blow()
        return is_blown

    @property
    def blown(self) -> bool:
        return self.__blown

    def blow(self) -> None:
        self.__blown = True