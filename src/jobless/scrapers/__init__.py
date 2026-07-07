import importlib
import pkgutil

_SKIP = {"base", "registry"}


def _load_all_scrapers() -> None:
    """Import every scraper module in this package so their @register decorators run.

    This is what makes adding a scraper "drop a file in this folder" - no
    registry file to edit, no import list to update.
    """
    for _, module_name, _ in pkgutil.iter_modules(__path__, prefix=f"{__name__}."):
        short_name = module_name.rsplit(".", 1)[-1]
        if short_name in _SKIP:
            continue
        importlib.import_module(module_name)


_load_all_scrapers()
