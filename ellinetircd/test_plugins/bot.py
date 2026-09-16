from ellinetircd.PluginAPI import GenericContext, PluginType
from ellinetircd.user import BotUser
import trio
import logging

logger = logging.getLogger(__name__)

PLUGIN_TYPE = PluginType.GENERIC
PLUGIN_NAME = "BOT test plugin"

async def setup(context: GenericContext):
    logger.info("Hello from the BOT test plugin!")

    async with trio.open_nursery() as nursery:
        async with BotUser(nursery) as bot:
            await bot.register("TestBot")
            await bot.join("#test")
            await bot.send_message("#test", f"Hello from TestBot!")