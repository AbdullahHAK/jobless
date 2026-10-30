from datetime import date

from jobless.scrapers.foodpanda import FoodpandaScraper

SITEMAP_XML = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url><loc>https://careers.foodpanda.com/job/manager-tax-in-karachi-pakistan-jid-3068</loc></url>
    <url><loc>https://careers.foodpanda.com/job/dc-specialist-in-karachi-pakistan-jid-3304</loc></url>
    <url><loc>https://careers.foodpanda.com/job/some-role-in-singapore-jid-9999</loc></url>
</urlset>
""".encode()

DETAIL_PAGES = {
    "https://careers.foodpanda.com/job/manager-tax-in-karachi-pakistan-jid-3068": (
        "<html><head><title>Manager Tax job in Karachi, Pakistan | foodpanda</title></head>"
        "<body></body></html>"
    ),
    "https://careers.foodpanda.com/job/dc-specialist-in-karachi-pakistan-jid-3304": (
        "<html><head><title>DC Specialist job in Karachi, Pakistan | foodpanda</title></head>"
        "<body></body></html>"
    ),
}


def test_scrape_keeps_only_pakistan_urls_and_parses_title_tag(mocker):
    def fake_get(url, **kwargs):
        if url.endswith("vacanciessitemap.xml"):
            return mocker.Mock(content=SITEMAP_XML, raise_for_status=lambda: None)
        return mocker.Mock(text=DETAIL_PAGES[url], raise_for_status=lambda: None)

    mock_get = mocker.patch("jobless.scrapers.foodpanda.requests.get", side_effect=fake_get)

    jobs = FoodpandaScraper().scrape()

    # 1 sitemap fetch + 2 Pakistan job detail fetches - the Singapore url is never fetched
    assert mock_get.call_count == 3
    assert len(jobs) == 2

    first = jobs[0]
    assert first.title == "Manager Tax"
    assert first.company == "foodpanda"
    assert first.location == "Karachi, Pakistan"
    assert str(first.apply_link) == "https://careers.foodpanda.com/job/manager-tax-in-karachi-pakistan-jid-3068"
    assert first.date_scraped == date.today()

    second = jobs[1]
    assert second.title == "DC Specialist"


def test_scrape_returns_empty_list_when_no_pakistan_urls(mocker):
    empty_sitemap = (
        b'<?xml version="1.0" encoding="UTF-8"?>'
        b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        b"<url><loc>https://careers.foodpanda.com/job/some-role-in-singapore-jid-1</loc></url>"
        b"</urlset>"
    )
    mock_get = mocker.patch(
        "jobless.scrapers.foodpanda.requests.get",
        return_value=mocker.Mock(content=empty_sitemap, raise_for_status=lambda: None),
    )

    jobs = FoodpandaScraper().scrape()

    assert mock_get.call_count == 1  # only the sitemap - no detail pages fetched
    assert jobs == []
