from ellinetircd.PluginAPI import GenericContext, PluginType
from ellinetircd.utils import shutdown
from ellinetircd.user import BotUser
import trio
import logging
import shlex

logger = logging.getLogger(__name__)

PLUGIN_TYPE = PluginType.GENERIC
PLUGIN_NAME = "OperServ"
PLUGIN_ID = "OperServ"

async def setup(context: GenericContext):
    async with trio.open_nursery() as nursery:
        async with BotUser(nursery) as bot:
            await bot.register("OperServ")
            async for user, channel, message in bot.messages():
                if channel:
                    continue

                if not "o" in user.modes:
                    await bot.send_message(user, "You must be an operator to use AdminServ.")
                    continue

                args = shlex.split(message)
                match args[0].lower():
                    case "shutdown":
                        await shutdown()
                        break

                    case _:
                        await bot.send_message(user, f"Unknown command: {args[0]}")
