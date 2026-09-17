from ellinetircd.PluginAPI import CommandContext, PluginType
from ellinetircd.utils import send_system_message
import logging

logger = logging.getLogger(__name__)

PLUGIN_TYPE = PluginType.COMMAND
PLUGIN_NAME = "COMMAND test plugin but in a folder"
PLUGIN_ID = "test_command_folder"

async def setup(context: CommandContext):
    logger.info("Hello from the COMMAND test plugin! (but it is in a folder)")

    @context.command
    async def FTEST(*args):
        await send_system_message(context.user, f"TEST command received with arguments: {args}")