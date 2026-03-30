import logging

import httpx

logger = logging.getLogger(__name__)

JINA_READER_URL = "https://r.jina.ai/"


class JinaScraper:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def scrape(self, url: str) -> str:
        """Scrape a URL using Jina Reader and return markdown."""
        logger.info("Scraping %s with Jina Reader", url)
        headers = {"Accept": "text/markdown"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        resp = httpx.get(f"{JINA_READER_URL}{url}", headers=headers, timeout=60)
        resp.raise_for_status()

        markdown = resp.text
        if not markdown.strip():
            raise ValueError(f"Jina Reader returned empty content for {url}")
        return markdown
