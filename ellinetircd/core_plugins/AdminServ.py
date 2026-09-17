from ellinetircd.PluginAPI import GenericContext, PluginType
from ellinetircd.user import BotUser
import trio
import logging
import shlex
import os
import signal

logger = logging.getLogger(__name__)

PLUGIN_TYPE = PluginType.GENERIC
PLUGIN_NAME = "AdminServ"
PLUGIN_ID = "AdminServ"

async def setup(context: GenericContext):
    async with trio.open_nursery() as nursery:
        async with BotUser(nursery) as bot:
            await bot.register("AdminServ")
            async for user, channel, message in bot.messages():
                if channel:
                    continue

                args = shlex.split(message)
                match args[0].lower:
                    case "shutdown":
                        os.kill(os.getpid(), signal.SIGINT)
                        break

                    case _:
                        await bot.send_message(user, f"Unknown command: {args[0]}")