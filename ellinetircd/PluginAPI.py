# Copyright (c) 2026 ElliNet13
# Licensed under the GNU General Public License v3.0 or later.

from enum import Enum
from collections.abc import Callable
from typing import TYPE_CHECKING, Optional, Type, Any
import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    import ellinetircd.plugins
    from ellinetircd.user import User

PluginType = Enum("PluginType", ["LANGUAGE", "COMMAND", "GENERIC"])

# Classes
class ContextBase:
    pass

class LanguageContext(ContextBase):
    def __init__(self, handlers: list[Language]):
        self._handlers = handlers

    def add_language(self, handler: Language):
        self._handlers.append(handler)

class Language:
    def __init__(self, context: LanguageContext):
        self._context = context

    def check(self, file_extension: str) -> bool:
        """Returns True if the file extension is handled by this language"""
        logger.error("A language must implement the check method!")
        return False

    def create_plugin(self, code: str, filename: str = "No name") -> ellinetircd.plugins.PluginBase:
        """Returns a plugin object from the given code"""
        raise NotImplementedError("A language must implement the create_plugin method!")

    @property
    def plugin_type_to_class(self) -> Callable[[PluginType], Optional[Type[ellinetircd.plugins.PluginBase]]]:
        from ellinetircd.plugins import plugin_type_to_class
        return plugin_type_to_class

    @property
    def check_required(self) -> Callable[[Any, dict[str, type | Any]], None]:
        from ellinetircd.plugins import check_required
        return check_required

class CommandContext(ContextBase):
    def __init__(self, command_decorator: Callable[[Callable], Callable], user: "User"):
        self._command_decorator = command_decorator
        self._user = user

    def command(self, command: Callable):
        return self._command_decorator(command)

    @property
    def user(self) -> "User":
        return self._user

class GenericContext(ContextBase):
    def __init__(self):
        pass
