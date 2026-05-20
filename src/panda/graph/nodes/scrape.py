import logging
import re

import httpx
from langchain_core.runnables import RunnableConfig

from panda.graph.context import NodeContext
from panda.graph.state import AgentState

logger = logging.getLogger(__name__)

DOI_PATTERN = re.compile(r"^10\.\d{4,9}/\S+$")


def resolve_doi(doi: str) -> str:
    """Resolve a DOI to its target URL via doi.org redirect."""
    resp = httpx.head(f"https://doi.org/{doi}", follow_redirects=True, timeout=30)
    return str(resp.url)


def scrape_node(state: AgentState, config: RunnableConfig) -> dict:
    """Scrape the publisher landing page and return markdown."""
    ctx = NodeContext(state, config)
    doi_or_url = state["doi_or_url"]

    # Resolve DOI to URL if needed
    if DOI_PATTERN.match(doi_or_url):
        try:
            page_url = resolve_doi(doi_or_url)
            logger.info("Resolved DOI %s -> %s", doi_or_url, page_url)
        except Exception as e:
            return {"error": f"Failed to resolve DOI: {e}", "status": "error"}
    else:
        page_url = doi_or_url

    ctx.update_status(":mag: Scraping publisher page...")

    # Try Firecrawl first, fall back to Jina
    from panda.scraper.firecrawl import FirecrawlScraper
    from panda.scraper.jina import JinaScraper

    try:
        markdown = FirecrawlScraper(api_key=ctx.settings.firecrawl_api_key).scrape(page_url)
    except Exception as e:
        logger.warning("Firecrawl failed (%s), falling back to Jina", e)
        if not ctx.settings.jina_api_key:
            return {"error": f"Scraping failed: {e}", "status": "error"}
        try:
            markdown = JinaScraper(api_key=ctx.settings.jina_api_key).scrape(page_url)
        except Exception as e2:
            return {"error": f"Both scrapers failed: {e2}", "status": "error"}

    return {"page_markdown": markdown, "page_url": page_url, "status": "scraped"}
