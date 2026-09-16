# Copyright (c) 2026 ElliNet13
# Licensed under the GNU General Public License v3.0 or later.

import importlib
import importlib.util
import pkgutil
import trio
from pathlib import Path
from types import ModuleType
from typing import Optional, Any
import logging
import traceback
import inspect

from ellinetircd.PluginAPI import PluginType, LanguageContext, CommandContext, GenericContext, Language

logger = logging.getLogger(__name__)


class PluginRequirementError(Exception):
    """Raised when a plugin does not meet its requirements."""


def check_required(
    module: Any,
    required: dict[str, type | Any],
) -> None:
    for name, expected in required.items():
        if not hasattr(module, name):
            raise PluginRequirementError(
                f"Plugin {module.__name__!r} is missing required "
                f"attribute {name!r}."
            )

        value = getattr(module, name)

        if expected is callable:
            if not callable(value):
                raise PluginRequirementError(
                    f"Plugin {module.__name__!r} attribute {name!r} "
                    f"must be callable, got {type(value).__name__}."
                )
        elif not isinstance(value, expected):
            raise PluginRequirementError(
                f"Plugin {module.__name__!r} attribute {name!r} "
                f"must be of type {expected.__name__}, "
                f"got {type(value).__name__}."
            )


def create_plugin(import_path: Optional[str] = None, module: Optional[ModuleType] = None) -> "PluginBase":
    """
    Build a plugin from a python module (given as an import path or an
    already-imported module). Non-python plugins don't go through here -
    they're built directly by a Language handler's create_plugin(), see
    _load_directory_other_plugins().
    """
    if import_path is not None and module is None:
        module = importlib.import_module(import_path)

    if module is None:
        raise ValueError("Either import_path or module must be provided.")

    check_required(module, {
        "setup": callable,
        "PLUGIN_TYPE": PluginType,
        "PLUGIN_NAME": str,
    })

    plugin_class = plugin_type_to_class(module.PLUGIN_TYPE)
    if plugin_class is None:
        raise PluginRequirementError(
            f"Plugin {module.PLUGIN_NAME!r} has unknown PLUGIN_TYPE "
            f"{module.PLUGIN_TYPE!r}."
        )

    return plugin_class(module.PLUGIN_NAME, module)


def plugin_type_to_class(plugin_type: PluginType) -> Optional[type["PluginBase"]]:
    if plugin_type == PluginType.LANGUAGE:
        return LanguagePlugin
    elif plugin_type == PluginType.COMMAND:
        return CommandPlugin
    elif plugin_type == PluginType.GENERIC:
        return GenericPlugin
    else:
        return None


def _load_package_plugins(package_name: str) -> list[ModuleType]:
    """Import every submodule of a plugin package (e.g. ellinetircd.core_plugins)."""
    modules: list[ModuleType] = []

    try:
        package = importlib.import_module(package_name)
    except ImportError:
        return modules

    package_path = getattr(package, "__path__", None)
    if package_path is None:
        return modules

    for module_info in pkgutil.iter_modules(package_path):
        if module_info.name.startswith("_"):
            continue

        full_name = f"{package_name}.{module_info.name}"
        try:
            modules.append(importlib.import_module(full_name))
        except Exception as exc:
            logger.error(f"Failed to import plugin {full_name!r}: {exc}")

    return modules


def _package_directory(package_name: str) -> Optional[Path]:
    """
    Resolve the on-disk directory backing an importable package, so its
    non-python plugin files (e.g. .lua) can be scanned the same way a
    ./plugins directory is. Returns None if the package can't be imported
    or has no filesystem location (e.g. a namespace/zip package).
    """
    try:
        package = importlib.import_module(package_name)
    except ImportError:
        return None

    package_path = getattr(package, "__path__", None)
    if not package_path:
        return None

    return Path(list(package_path)[0])


def _load_directory_plugins(directory: Path) -> list[ModuleType]:
    """Import every top-level .py file in an arbitrary directory (not a package)."""
    modules: list[ModuleType] = []

    if not directory.is_dir():
        return modules

    for path in sorted(directory.glob("*.py")):
        if path.stem.startswith("_"):
            continue

        module_name = f"_external_plugin_{directory.name}_{path.stem}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        if spec is None or spec.loader is None:
            continue

        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except Exception as exc:
            logger.error(f"Failed to import plugin {path!r}: {exc}")
            continue

        modules.append(module)

    return modules


def _load_directory_other_plugins(
    directory: Path,
    language_handlers: list[Language],
) -> list["PluginBase"]:
    """
    Scan ``directory`` for non-python plugin files and build a plugin for
    each one whose extension is claimed by a Language handler.

    This only runs after every python plugin has been discovered and every
    LANGUAGE plugin among them has had a chance to register a handler -
    python is always checked first, other languages are opt-in on top.
    """
    other_plugins: list["PluginBase"] = []

    if not directory.is_dir() or not language_handlers:
        return other_plugins

    for path in sorted(directory.iterdir()):
        if not path.is_file() or path.suffix == ".py" or path.stem.startswith("_"):
            continue

        handler = next((h for h in language_handlers if h.check(path.suffix)), None)
        if handler is None:
            logger.debug("No language handler claims %s, skipping.", path)
            continue

        try:
            other_plugins.append(handler.create_plugin(path.read_text(), str(path)))
        except Exception as exc:
            logger.error(f"Failed to load plugin {path!r} via language handler:")
            traceback.print_exc()
            continue

    return other_plugins


def _collect_language_handlers(plugins: list["PluginBase"]) -> list[Language]:
    """
    Run setup() on every LANGUAGE plugin in ``plugins`` so it can register
    its Language handler via the LanguageContext it's given, and return
    everything that got registered.
    """
    handlers: list[Language] = []
    context = LanguageContext(handlers)

    for plugin in plugins:
        if not isinstance(plugin, LanguagePlugin):
            continue
        try:
            trio.run(plugin.load, context)
        except Exception:
            logger.error(f"Failed to initialize language plugin {plugin.name!r}:")
            traceback.print_exc()

    return handlers


def _load_python_plugins(
    package_name: Optional[str] = None,
    directory: Optional[Path] = None,
) -> list["PluginBase"]:
    """
    Load python plugins from an importable package and/or an arbitrary
    directory, turning every discovered module into a PluginBase.
    """
    modules: list[ModuleType] = []

    if package_name is not None:
        modules.extend(_load_package_plugins(package_name))

    if directory is not None:
        modules.extend(_load_directory_plugins(directory))

    plugins: list["PluginBase"] = []
    for module in modules:
        try:
            plugins.append(create_plugin(module=module))
        except (PluginRequirementError, ValueError) as exc:
            logger.error(f"Skipping invalid plugin {getattr(module, '__name__', module)!r}:")
            traceback.print_exc()
            continue

    return plugins


def find_all_plugins() -> list["PluginBase"]:
    """
    Discover plugins from three sources, in order:

    1. The `core_plugins` package bundled inside `ellinetircd`.
    2. The `test_plugins` package inside `ellinetircd`, but only when
       `ellinetircd` itself is installed in editable mode (`pip install -e`).
    3. A `./plugins` directory relative to the current working directory,
       if one exists.

    Each source is loaded in two passes: `.py` files first (always), then
    any other file extension claimed by a Language handler that a LANGUAGE
    plugin - from this source or an earlier one - has registered by that
    point. This lets a LANGUAGE plugin shipped in core_plugins enable e.g.
    .lua plugins sitting in test_plugins or ./plugins, and a LANGUAGE
    plugin dropped in ./plugins enable other .lua files in that same
    directory.
    """
    found_plugins: list["PluginBase"] = []
    language_handlers: list[Language] = []
    editable_install = logger.isEnabledFor(logging.DEBUG)

    logger.debug("Discovering plugins...")

    sources: list[tuple[Optional[str], Optional[str], bool]] = [
        ("ellinetircd.core_plugins", None, True),
        ("ellinetircd.test_plugins", None, editable_install),
        (None, "plugins", True),
    ]

    for package_name, cwd_subdir, enabled in sources:
        if not enabled:
            continue

        directory = Path.cwd() / cwd_subdir if cwd_subdir else _package_directory(package_name) # pyright: ignore[reportArgumentType]

        logger.debug(
            "Loading plugins from %s...",
            package_name or directory,
        )

        # Pass 1: python plugins for this source.
        py_plugins = _load_python_plugins(package_name=package_name, directory=directory)
        found_plugins.extend(py_plugins)

        # Any LANGUAGE plugin just loaded (from this source or accumulated
        # from earlier ones) can now claim non-python files.
        language_handlers += _collect_language_handlers(py_plugins)

        # Pass 2: non-python plugins for this source's directory, using
        # every handler registered so far.
        if directory is not None:
            found_plugins.extend(_load_directory_other_plugins(directory, language_handlers))

    logger.debug("Discovered %d plugins.", len(found_plugins))

    return found_plugins


class PluginBase:
    def __init__(self, name: str, module):
        self.name = name
        self.module = module

    async def load(self, context):
        if not inspect.iscoroutinefunction(self.module.setup):
            logger.error(f"Plugin {self.name!r} does not have a coroutine setup() method.")
            return
        await self.module.setup(context)

class LanguagePlugin(PluginBase):
    async def load(self, language_context: LanguageContext):
        await super().load(language_context)

class CommandPlugin(PluginBase):
    async def load(self, command_context: CommandContext):
        await super().load(command_context)

class GenericPlugin(PluginBase):
    async def load(self, generic_context: GenericContext):
        await super().load(generic_context)