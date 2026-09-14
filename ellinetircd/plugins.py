import asyncio
import importlib
import importlib.util
import json
import pkgutil
from importlib import metadata
from pathlib import Path
from types import ModuleType
from typing import Optional, Any

from ellinetircd.PluginAPI import PluginType, LanguageContext, CommandContext

class PluginRequirementError(Exception):
    """Raised when a plugin does not meet its requirements."""


def check_required(
    module: ModuleType,
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


def create_plugin(import_path: Optional[str], module: Optional[ModuleType]) -> "PluginBase":
    if import_path is not None and module is None:
        module = importlib.import_module(import_path)

    if module is None:
        raise ValueError("Either import_path or module must be provided.")

    check_required(module, {
        "setup": callable,
        "PLUGIN_TYPE": PluginType,
    })

    if module.PLUGIN_TYPE == PluginType.LANGUAGE:
        return LanguagePlugin(module.__name__, module)
    elif module.PLUGIN_TYPE == PluginType.COMMAND:
        return CommandPlugin(module.__name__, module)
    else:
        raise PluginRequirementError(
            f"Plugin {module.__name__!r} has unknown PLUGIN_TYPE "
            f"{module.PLUGIN_TYPE!r}."
        )


def _is_editable_install(package_name: str) -> bool:
    """Best-effort check for whether a package is installed in editable mode.

    Relies on the PEP 660 `direct_url.json` metadata file, which pip writes
    with `"editable": true` under `dir_info` for `pip install -e` installs.
    """
    try:
        dist = metadata.distribution(package_name)
    except metadata.PackageNotFoundError:
        return False

    try:
        raw = dist.read_text("direct_url.json")
    except Exception:
        raw = None

    if not raw:
        return False

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return False

    return bool(data.get("dir_info", {}).get("editable", False))


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
            print(f"Failed to import plugin {full_name!r}: {exc}")

    return modules


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
            print(f"Failed to import plugin {path!r}: {exc}")
            continue

        modules.append(module)

    return modules


def find_all_plugins() -> list["PluginBase"]:
    """Discover plugins from:

    1. The `core_plugins` package bundled inside `ellinetircd`.
    2. A `./plugins` directory relative to the current working directory,
       if one exists (arbitrary .py files, not required to be a package).
    3. The `test_plugins` package inside `ellinetircd`, but only when
       `ellinetircd` itself is installed in editable mode (`pip install -e`).
    """
    discovered_modules: list[ModuleType] = []

    # 1. core_plugins folder shipped inside the ellinetircd package.
    discovered_modules.extend(_load_package_plugins("ellinetircd.core_plugins"))

    # 2. ./plugins relative to the current working directory, if it exists.
    cwd_plugins_dir = Path.cwd() / "plugins"
    discovered_modules.extend(_load_directory_plugins(cwd_plugins_dir))

    # 3. test_plugins folder inside the ellinetircd package, editable installs only.
    if _is_editable_install("ellinetircd"):
        discovered_modules.extend(_load_package_plugins("ellinetircd.test_plugins"))

    found_plugins: list["PluginBase"] = []
    for module in discovered_modules:
        try:
            found_plugins.append(create_plugin(None, module))
        except (PluginRequirementError, ValueError) as exc:
            print(f"Skipping invalid plugin {getattr(module, '__name__', module)!r}: {exc}")

    return found_plugins


class PluginBase:
    def __init__(self, name: str, module):
        self.name = name
        self.module = module

    async def _load(self, *args, **kwargs):
        asyncio.create_task(self.module.setup(*args, **kwargs))


class LanguagePlugin(PluginBase):
    async def load(self, language_context: LanguageContext):
        await super()._load(language_context)


class CommandPlugin(PluginBase):
    async def load(self, command_context: CommandContext):
        await super()._load(command_context)