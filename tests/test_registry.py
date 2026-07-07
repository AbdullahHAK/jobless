from jobless.scrapers.base import Job, Scraper
from jobless.scrapers.registry import all_scrapers, register


def test_register_adds_scraper_to_registry():
    @register
    class DummyScraper(Scraper):
        company_name = "Dummy Co"

        def scrape(self) -> list[Job]:
            return []

    assert DummyScraper in all_scrapers()


def test_arbisoft_scraper_is_auto_registered():
    import jobless.scrapers  # noqa: F401 - triggers auto-discovery

    names = [cls.company_name for cls in all_scrapers()]
    assert "Arbisoft" in names
