from enum import Enum
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ellinetircd.user import User

PluginType = Enum("PluginType", ["LANGUAGE", "COMMAND"])

class LanguageContext:
    def __init__(self, handlers: list[Callable]):
        self._handlers = handlers

    def add_handler(self, handler: Callable[[str], None]):
        self._handlers.append(handler)
        return handler

class CommandContext:
    def __init__(self, command_decorator: Callable[[Callable], Callable], user: "User"):
        self._command_decorator = command_decorator
        self._user = user

    def command(self, command: Callable):
        return self._command_decorator(command)

    @property
    def user(self) -> "User":
        return self._user