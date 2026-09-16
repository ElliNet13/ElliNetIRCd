from ellinetircd.PluginAPI import PluginType, LanguageContext, Language, CommandContext
from ellinetircd.utils import send_system_message
import ellinetircd.plugins
import logging

logger = logging.getLogger(__name__)

PLUGIN_TYPE = PluginType.LANGUAGE
PLUGIN_NAME = "LANGUAGE test plugin"

class TestCommandPlugin():
    PLUGIN_TYPE = PluginType.LANGUAGE
    PLUGIN_NAME = "LANGUAGE test plugin"

    async def setup(self, context: CommandContext):
        logger.info("Hello from the COMMAND test plugin from LANGUAGE test plugin!")

        @context.command
        async def LTEST(*args):
            await send_system_message(context.user, f"LTEST command received with arguments: {args}")

async def setup(context: LanguageContext):
    logger.info("Hello from the LANGUAGE test plugin!")

    class TestLanguage(Language):
        def check(self, file_extension: str) -> bool:
            return file_extension == ".test"

        def create_plugin(self, code: str, filename: str = "No name") -> "ellinetircd.plugins.PluginBase":
            return ellinetircd.plugins.CommandPlugin("Test command via test language", TestCommandPlugin())

    context.add_language(TestLanguage())