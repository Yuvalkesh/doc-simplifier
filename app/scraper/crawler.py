import httpx
from urllib.parse import urljoin, urlparse
from typing import Set, List
from bs4 import BeautifulSoup

class DocumentationCrawler:
    def __init__(self, max_depth: int = 1, max_pages: int = 3):
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.visited: Set[str] = set()
        self.pages: List[dict] = []

    async def crawl(self, start_url: str, progress_callback=None) -> List[dict]:
        await self._crawl_page(start_url, 0)
        return self.pages

    async def _crawl_page(self, url: str, depth: int):
        url = url.split("#")[0].rstrip("/")
        if url in self.visited or depth > self.max_depth or len(self.pages) >= self.max_pages:
            return
        self.visited.add(url)
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers={"User-Agent": "DocSimplifier/1.0"}) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                if "text/html" not in resp.headers.get("content-type", ""):
                    return
                soup = BeautifulSoup(resp.text, "lxml")
                title = soup.title.string if soup.title else (soup.find("h1").get_text(strip=True) if soup.find("h1") else "")
                content = self._extract(soup)
                if content and len(content) > 100:
                    self.pages.append({"url": url, "title": title, "content": content, "depth": depth})
                if depth < self.max_depth and len(self.pages) < self.max_pages:
                    for link in self._links(soup, url)[:2]:
                        await self._crawl_page(link, depth + 1)
        except Exception as e:
            print(f"Crawl error {url}: {e}")

    def _extract(self, soup: BeautifulSoup) -> str:
        for t in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
            t.decompose()
        main = None
        for sel in ["main", "article", "[role='main']", ".content", ".documentation", "#content"]:
            main = soup.select_one(sel)
            if main:
                break
        if not main:
            main = soup.body or soup
        parts = []
        for el in main.find_all(["h1", "h2", "h3", "h4", "p", "li", "pre", "code"]):
            txt = el.get_text(strip=True)
            if not txt:
                continue
            if el.name in ["h1", "h2", "h3", "h4"]:
                parts.append(f"\n## {txt}\n")
            elif el.name == "li":
                parts.append(f"- {txt}")
            elif el.name in ["pre", "code"] and len(txt) < 300:
                parts.append(f"```\n{txt}\n```")
            else:
                parts.append(txt)
        return "\n".join(parts)

    def _links(self, soup: BeautifulSoup, current: str) -> List[str]:
        base = urlparse(current).netloc
        links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if href.startswith("#") or href.startswith("javascript:"):
                continue
            full = urljoin(current, href)
            if urlparse(full).netloc != base:
                continue
            skip = ["/blog", "/login", "/signup", "/pricing", ".pdf", ".zip"]
            if any(s in full.lower() for s in skip):
                continue
            links.append(full.split("#")[0])
        return list(set(links))[:3]
