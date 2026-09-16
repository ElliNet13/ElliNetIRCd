# Copyright (c) 2026 ElliNet13
# Licensed under the GNU General Public License v3.0 or later.

from ellinetircd.PluginAPI import PluginType, LanguageContext, Language
import ellinetircd.plugins
import logging
from typing import Callable, Optional

logger = logging.getLogger(__name__)

PLUGIN_TYPE = PluginType.LANGUAGE
PLUGIN_NAME = "Lua language support"

try:
    import lupa.luajit21 as lupa
except ImportError:
    try:
        import lupa.lua54 as lupa
    except ImportError:
        try:
            import lupa.lua53 as lupa
        except ImportError:
            import lupa

def setup_lua_environment(filename: str = "No name"):
    lua = lupa.LuaRuntime() # pyright: ignore[reportCallIssue]
    globals = lua.globals()

    Enums = {
        "PluginType": PluginType
    }

    setattr(globals, "Enum", Enums)
    setattr(globals, "logger", logging.getLogger(filename))

    return lua

logger.debug(f"Lua language support is using: {setup_lua_environment().lua_implementation} (compiled with {lupa.LUA_VERSION})")

class LuaCommandContext(ellinetircd.plugins.CommandContext):
    def command(self, name: str, command: Callable):
        async def wrapper(*args, **kwargs):
            return command(self.user, *args, **kwargs)
        wrapper.__name__ = name
        return super().command(wrapper)

class LuaCommandPlugin(ellinetircd.plugins.CommandPlugin):
    def load(self, context: ellinetircd.plugins.CommandContext):
        return super().load(command_context_to_lua(context))

def command_context_to_lua(context: ellinetircd.plugins.CommandContext) -> LuaCommandContext:
    return LuaCommandContext(context.command, context.user)

async def setup(context: LanguageContext):
    class LuaLanguage(Language):
        def check(self, file_extension: str) -> bool:
            return file_extension == ".lua"

        def create_plugin(self, code: str, filename: str = "No name") -> "ellinetircd.plugins.PluginBase":
            lua = setup_lua_environment(filename)
            try:
                lua.execute(code)
            except lupa.LuaError as e:
                raise ellinetircd.plugins.PluginRequirementError(f"Failed to load plugin: {e}")
            globals = lua.globals()

            self.check_required(globals, {"PLUGIN_TYPE": PluginType, "PLUGIN_NAME": str, "setup": Callable})
            name = getattr(globals, "PLUGIN_NAME")

            sync_setup = getattr(globals, "setup")

            async def async_setup(context):
                sync_setup(context)

            setattr(globals, "setup", async_setup)

            plugin_type = self.plugin_type_to_class(getattr(globals, "PLUGIN_TYPE"))

            if plugin_type is None:
                raise ellinetircd.plugins.PluginRequirementError(
                    f"Plugin {name!r} has unknown PLUGIN_TYPE "
                    f"{name!r}."
                )

            return plugin_type(name, globals)
        
        @property
        def plugin_type_to_class(self):
            plugin_type_to_class = super().plugin_type_to_class
            def new_plugin_type_to_class(plugin_type: PluginType) -> Optional[type["ellinetircd.plugins.PluginBase"]]:
                source = plugin_type_to_class(plugin_type)
                match source:
                    case ellinetircd.plugins.CommandPlugin:
                        return LuaCommandPlugin
                    case _:
                        return source
            return new_plugin_type_to_class

    context.add_language(LuaLanguage(context))