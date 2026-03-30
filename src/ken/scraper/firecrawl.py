import logging

from firecrawl import FirecrawlApp

logger = logging.getLogger(__name__)


class FirecrawlScraper:
    def __init__(self, api_key: str):
        self.client = FirecrawlApp(api_key=api_key)

    def scrape(self, url: str) -> str:
        """Scrape a URL using Firecrawl and return markdown."""
        logger.info("Scraping %s with Firecrawl", url)
        result = self.client.scrape_url(url, params={"formats": ["markdown"]})
        markdown = result.get("markdown", "")
        if not markdown:
            raise ValueError(f"Firecrawl returned empty markdown for {url}")
        return markdown
