import httpx
import asyncio
from urllib.parse import urljoin, urlparse
from typing import Set, List, Optional
from bs4 import BeautifulSoup
import re


class DocumentationCrawler:
    """Crawl documentation sites and extract content."""

    def __init__(self, max_depth: int = 3, max_pages: int = 50):
        self.max_depth = max_depth
        self.max_pages = max_pages
        self.visited: Set[str] = set()
        self.pages: List[dict] = []
        self.base_domain: str = ""
        self.base_path: str = ""

    async def crawl(self, start_url: str, progress_callback=None) -> List[dict]:
        """
        Crawl starting from the given URL.

        Args:
            start_url: The starting URL to crawl
            progress_callback: Optional async callback for progress updates

        Returns:
            List of crawled pages with url, title, and content
        """
        parsed = urlparse(start_url)
        self.base_domain = parsed.netloc
        self.base_path = parsed.path.rsplit("/", 1)[0] if "/" in parsed.path else ""

        await self._crawl_page(start_url, 0, progress_callback)

        return self.pages

    async def _crawl_page(self, url: str, depth: int, progress_callback=None):
        """Recursively crawl a page and its links."""
        # Normalize URL
        url = url.split("#")[0]  # Remove fragments
        url = url.rstrip("/")

        # Check limits
        if url in self.visited:
            return
        if depth > self.max_depth:
            return
        if len(self.pages) >= self.max_pages:
            return

        self.visited.add(url)

        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; DocSimplifier/1.0)"
                }
            ) as client:
                response = await client.get(url)
                response.raise_for_status()

                # Only process HTML pages
                content_type = response.headers.get("content-type", "")
                if "text/html" not in content_type:
                    return

                html = response.text
                soup = BeautifulSoup(html, "lxml")

                # Extract title
                title = ""
                if soup.title:
                    title = soup.title.string or ""
                elif soup.find("h1"):
                    title = soup.find("h1").get_text(strip=True)

                # Extract main content
                content = self._extract_content(soup)

                if content and len(content) > 100:  # Skip empty pages
                    self.pages.append({
                        "url": url,
                        "title": title,
                        "content": content,
                        "depth": depth
                    })

                    if progress_callback:
                        await progress_callback(
                            10 + min(len(self.pages) * 2, 30),
                            f"Crawled {len(self.pages)} pages..."
                        )

                # Find and crawl links
                if depth < self.max_depth:
                    links = self._extract_links(soup, url)
                    tasks = []
                    for link in links[:20]:  # Limit concurrent crawls
                        if link not in self.visited:
                            tasks.append(
                                self._crawl_page(link, depth + 1, progress_callback)
                            )

                    # Crawl with some concurrency control
                    for i in range(0, len(tasks), 5):
                        batch = tasks[i:i+5]
                        await asyncio.gather(*batch, return_exceptions=True)
                        await asyncio.sleep(0.5)  # Rate limiting

        except httpx.HTTPError as e:
            print(f"HTTP error crawling {url}: {e}")
        except Exception as e:
            print(f"Error crawling {url}: {e}")

    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from the page."""
        # Remove script, style, nav, footer elements
        for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # Try to find main content area
        main_content = None

        # Common documentation content containers
        selectors = [
            "main",
            "article",
            "[role='main']",
            ".content",
            ".documentation",
            ".docs-content",
            ".markdown-body",
            "#content",
            "#main-content",
            ".main-content",
        ]

        for selector in selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break

        if not main_content:
            main_content = soup.body if soup.body else soup

        # Extract text with some structure preserved
        text_parts = []
        for element in main_content.find_all(["h1", "h2", "h3", "h4", "p", "li", "pre", "code"]):
            tag_name = element.name
            text = element.get_text(strip=True)

            if not text:
                continue

            if tag_name in ["h1", "h2", "h3", "h4"]:
                text_parts.append(f"\n\n## {text}\n")
            elif tag_name == "li":
                text_parts.append(f"- {text}")
            elif tag_name in ["pre", "code"]:
                # Keep code blocks but mark them
                if len(text) < 500:  # Skip very long code blocks
                    text_parts.append(f"\n```\n{text}\n```\n")
            else:
                text_parts.append(text)

        return "\n".join(text_parts)

    def _extract_links(self, soup: BeautifulSoup, current_url: str) -> List[str]:
        """Extract relevant links from the page."""
        links = []

        for a in soup.find_all("a", href=True):
            href = a["href"]

            # Skip anchors, javascript, and external links
            if href.startswith("#") or href.startswith("javascript:"):
                continue

            # Make absolute URL
            full_url = urljoin(current_url, href)
            parsed = urlparse(full_url)

            # Only follow links within same domain
            if parsed.netloc != self.base_domain:
                continue

            # Stay within the documentation path if possible
            if self.base_path and not parsed.path.startswith(self.base_path):
                # Allow one level up from base path
                parent_path = self.base_path.rsplit("/", 1)[0]
                if parent_path and not parsed.path.startswith(parent_path):
                    continue

            # Skip common non-doc paths
            skip_patterns = [
                "/blog", "/news", "/press", "/careers", "/about",
                "/login", "/signup", "/pricing", "/contact",
                ".pdf", ".zip", ".tar", ".gz"
            ]
            if any(pattern in full_url.lower() for pattern in skip_patterns):
                continue

            links.append(full_url.split("#")[0])

        return list(set(links))  # Remove duplicates
