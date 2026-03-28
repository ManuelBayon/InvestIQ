import importlib
import pkgutil
from types import ModuleType
from typing import List


def import_submodules(
        package_name: str
) -> List[ModuleType]:
    """
    Dynamically import all submodules of a given package.

    HF-grade utility for auto-discovering strategies/rules/guards
    without having to maintain manual imports.

    Args:
        package_name: The full dotted path of the package
                      (e.g. "backtest_engine.transition_engine.rules.rules")

    Returns:
        List of loaded module objects.
    """
    package = importlib.import_module(package_name)
    imported_modules: List[ModuleType] = []

    for _, module_name, _ in pkgutil.walk_packages(package.__path__, package.__name__ + "."):
        imported_modules.append(importlib.import_module(module_name))

    return imported_modules
