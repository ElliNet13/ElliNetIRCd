PLUGIN_TYPE = Enum.PluginType.COMMAND
PLUGIN_NAME = "Lua COMMAND test plugin"
PLUGIN_ID = "LUA_COMMAND"

function setup(context)
    logger.info("Hello from the COMMAND test plugin!")

    context.command("LUATEST", function(...)
        local arguments = {...}

        send_system_message(
            context.user,
            "TEST command received with arguments: " .. table.concat(arguments, ", ")
        )
    end)
end