from ellinetircd.PluginAPI import CommandContext, PluginType
from ellinetircd.utils import send_system_message
import logging

logger = logging.getLogger(__name__)

PLUGIN_TYPE = PluginType.COMMAND
PLUGIN_NAME = "COMMAND test plugin"

async def setup(context: CommandContext):
    logger.info("Hello from the COMMAND test plugin!")

    @context.command
    async def TEST(*args):
        await send_system_message(context.user, f"TEST command received with arguments: {args}")