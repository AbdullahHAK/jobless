from .base import Scraper

_registry: dict[str, type[Scraper]] = {}


def register(scraper_cls: type[Scraper]) -> type[Scraper]:
    """Class decorator: add a Scraper subclass to the registry by company_name."""
    _registry[scraper_cls.company_name] = scraper_cls
    return scraper_cls


def all_scrapers() -> list[type[Scraper]]:
    return list(_registry.values())
