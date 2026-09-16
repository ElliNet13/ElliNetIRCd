# Copyright (c) 2026 ElliNet13
# Licensed under the GNU General Public License v3.0 or later.

from typing import TYPE_CHECKING

import ellinetircd

if TYPE_CHECKING:
    from ellinetircd.user import User
    from ellinetircd.server import ServLocal

async def send_system_message(user: "User", messages: str|list[str]) -> None:
    servlocal: "ServLocal" = ellinetircd.servlocal.get()

    if type(messages) == str:
        messages_new = [messages]

    for i, message in enumerate(messages_new):
        messages_new[i] = f":{servlocal.host} NOTICE {user.nick} :{message}"

    await user.send(messages_new)