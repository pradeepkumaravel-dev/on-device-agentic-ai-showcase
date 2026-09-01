import logging

import trafilatura
from ddgs import DDGS
from langchain_core.tools import tool
from src.utilities.exception_utils import NormalExceptions

logger = logging.getLogger(__name__)

MAX_PAGE_CHARS = 4000


@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web for current information. Returns a list of results, each
    with a title, URL, and short snippet. Use fetch_page on the most promising
    URLs to read the full article before writing a comprehensive report."""
    try:
        results = DDGS().text(query, max_results=max_results)
        if not results:
            return "No results found."
        return "\n\n".join(
            f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}" for r in results
        )
    except NormalExceptions:
        raise
    except Exception as e:
        raise NormalExceptions(message="exception occurred in research_tools.py:web_search", error=str(e), log=True)


@tool
def fetch_page(url: str) -> str:
    """Fetch a web page and extract its main readable text content, stripping
    ads/navigation/boilerplate. Use after web_search to read full articles for
    a comprehensive report. Content is truncated to a few thousand characters."""
    try:
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            return f"Could not fetch {url}"
        text = trafilatura.extract(downloaded)
        if not text:
            return f"Could not extract readable content from {url}"
        if len(text) > MAX_PAGE_CHARS:
            text = text[:MAX_PAGE_CHARS] + "... [truncated]"
        return text
    except NormalExceptions:
        raise
    except Exception as e:
        raise NormalExceptions(message="exception occurred in research_tools.py:fetch_page", error=str(e), log=True)
