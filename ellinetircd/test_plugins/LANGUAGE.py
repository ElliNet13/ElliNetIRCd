from ellinetircd.PluginAPI import PluginType, LanguageContext

PLUGIN_TYPE = PluginType.LANGUAGE

def setup(context: LanguageContext):
    print("Hello from the LANGUAGE test plugin!")