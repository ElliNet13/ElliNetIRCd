from ellinetircd.PluginAPI import PluginType, LanguageContext
import logging

logger = logging.getLogger(__name__)

PLUGIN_TYPE = PluginType.LANGUAGE
PLUGIN_NAME = "LANGUAGE test plugin"

async def setup(context: LanguageContext):
    logger.info("Hello from the LANGUAGE test plugin!")