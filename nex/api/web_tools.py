"""Web tools — DuckDuckGo search and webpage fetching."""

import re
import httpx

SEARCH_URL = "https://html.duckduckgo.com/html/"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Nex/0.1"
TIMEOUT = 15.0


async def web_search(query: str, max_results: int = 5) -> str:
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        resp = await client.post(SEARCH_URL, data={"q": query}, headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()
    html = resp.text
    links = re.findall(r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>', html, re.DOTALL)
    snips = re.findall(r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>', html, re.DOTALL)
    if not links:
        return f"No results found for '{query}'."
    results = []
    for i, (url, title) in enumerate(links[:max_results]):
        t = re.sub(r'<[^>]+>', '', title).strip()
        s = re.sub(r'<[^>]+>', '', snips[i]).strip() if i < len(snips) else ""
        results.append(f"{i+1}. {t}\n   {url}\n   {s}")
    return f"Search results for '{query}':\n\n" + "\n\n".join(results)


async def fetch_webpage(url: str, max_chars: int = 3000) -> str:
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        resp = await client.get(url, headers={"User-Agent": USER_AGENT})
        resp.raise_for_status()
    html = resp.text
    html = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) > max_chars:
        text = text[:max_chars] + "... (truncated)"
    return text if text else "(Page had no readable text content)"
