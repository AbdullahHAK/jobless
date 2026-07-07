from abc import ABC, abstractmethod
from datetime import date

from pydantic import BaseModel, HttpUrl


class Job(BaseModel):
    """The standard job schema every scraper must produce."""

    title: str
    company: str
    location: str
    apply_link: HttpUrl
    date_scraped: date


class Scraper(ABC):
    """Interface every company scraper must implement."""

    company_name: str

    @abstractmethod
    def scrape(self) -> list[Job]:
        """Fetch and return all currently open jobs for this company."""
