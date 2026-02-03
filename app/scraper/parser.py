from bs4 import BeautifulSoup
from typing import Optional
import re


class ContentParser:
    """Parse and extract structured content from HTML."""

    @staticmethod
    def extract_title(soup: BeautifulSoup) -> str:
        """Extract the page title."""
        if soup.title and soup.title.string:
            return soup.title.string.strip()

        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)

        return "Untitled Document"

    @staticmethod
    def extract_description(soup: BeautifulSoup) -> Optional[str]:
        """Extract meta description or first paragraph."""
        # Try meta description
        meta = soup.find("meta", attrs={"name": "description"})
        if meta and meta.get("content"):
            return meta["content"]

        # Try first paragraph
        p = soup.find("p")
        if p:
            text = p.get_text(strip=True)
            if len(text) > 50:
                return text

        return None

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean extracted text."""
        # Remove excessive whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)

        # Remove common noise
        noise_patterns = [
            r"Cookie.*?policy",
            r"Subscribe.*?newsletter",
            r"Follow us on",
            r"Share this",
            r"Was this.*?helpful",
        ]

        for pattern in noise_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        return text.strip()

    @staticmethod
    def extract_code_examples(soup: BeautifulSoup) -> list:
        """Extract code examples from the page."""
        examples = []

        for code_block in soup.find_all(["pre", "code"]):
            code = code_block.get_text(strip=True)
            if len(code) > 20 and len(code) < 2000:
                # Try to detect language
                classes = code_block.get("class", [])
                lang = None
                for cls in classes:
                    if cls.startswith("language-"):
                        lang = cls.replace("language-", "")
                        break

                examples.append({
                    "code": code,
                    "language": lang
                })

        return examples[:10]  # Limit to 10 examples

    @staticmethod
    def extract_sections(soup: BeautifulSoup) -> list:
        """Extract document sections based on headers."""
        sections = []
        current_section = {"title": "Introduction", "content": []}

        content_area = soup.find("main") or soup.find("article") or soup.body

        if not content_area:
            return sections

        for element in content_area.find_all(["h1", "h2", "h3", "p", "ul", "ol", "pre"]):
            if element.name in ["h1", "h2", "h3"]:
                if current_section["content"]:
                    sections.append(current_section)
                current_section = {
                    "title": element.get_text(strip=True),
                    "content": []
                }
            else:
                text = element.get_text(strip=True)
                if text:
                    current_section["content"].append(text)

        if current_section["content"]:
            sections.append(current_section)

        return sections
