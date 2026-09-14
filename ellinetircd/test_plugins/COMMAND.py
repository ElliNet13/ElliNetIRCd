from ellinetircd.PluginAPI import CommandContext, PluginType

PLUGIN_TYPE = PluginType.COMMAND

def setup(context: CommandContext):
    print("Hello from the COMMAND test plugin!")