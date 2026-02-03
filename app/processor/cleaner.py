import re
from typing import List


class ContentCleaner:
    """Clean and prepare content for AI processing."""

    @staticmethod
    def clean_content(pages: List[dict]) -> str:
        """
        Clean and combine content from multiple pages.

        Args:
            pages: List of page dicts with url, title, content

        Returns:
            Cleaned combined content string
        """
        cleaned_parts = []

        for page in pages:
            title = page.get("title", "")
            content = page.get("content", "")

            # Clean the content
            content = ContentCleaner._clean_text(content)

            if content and len(content) > 100:
                cleaned_parts.append(f"# {title}\n\n{content}")

        combined = "\n\n---\n\n".join(cleaned_parts)

        # Final cleanup
        combined = ContentCleaner._remove_duplicates(combined)

        return combined

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean individual text content."""
        # Remove excessive whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        text = re.sub(r"\t+", " ", text)

        # Remove common UI noise
        noise_patterns = [
            r"Cookie.*?(?:policy|consent|preferences)",
            r"Subscribe.*?newsletter",
            r"Follow us on.*?(?:Twitter|Facebook|LinkedIn)",
            r"Share this.*?(?:article|page)",
            r"Was this.*?helpful\??",
            r"(?:Previous|Next) (?:article|page)",
            r"Table of [Cc]ontents",
            r"On this page",
            r"Skip to.*?content",
            r"Edit this page.*?GitHub",
            r"Last updated:.*?\d{4}",
            r"Reading time:.*?min",
        ]

        for pattern in noise_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE | re.DOTALL)

        # Clean up navigation artifacts
        text = re.sub(r"^[-•]\s*$", "", text, flags=re.MULTILINE)

        # Remove very short lines that are likely navigation
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            # Keep headers and meaningful content
            if line.startswith("#") or len(line) > 20 or line.startswith("- "):
                cleaned_lines.append(line)
            elif line.startswith("```") or line.endswith("```"):
                cleaned_lines.append(line)

        text = "\n".join(cleaned_lines)

        return text.strip()

    @staticmethod
    def _remove_duplicates(text: str) -> str:
        """Remove duplicate paragraphs that appear across pages."""
        paragraphs = text.split("\n\n")
        seen = set()
        unique_paragraphs = []

        for para in paragraphs:
            # Normalize for comparison
            normalized = para.strip().lower()
            if len(normalized) < 50:  # Keep short paragraphs (might be headers)
                unique_paragraphs.append(para)
            elif normalized not in seen:
                seen.add(normalized)
                unique_paragraphs.append(para)

        return "\n\n".join(unique_paragraphs)

    @staticmethod
    def simplify_code_blocks(text: str) -> str:
        """Simplify or summarize code blocks for non-technical readers."""
        def replace_code(match):
            code = match.group(1)
            lines = code.strip().split("\n")

            if len(lines) > 10:
                # Summarize long code blocks
                return f"\n[Code example with {len(lines)} lines]\n"
            elif len(lines) > 5:
                # Show first few lines
                preview = "\n".join(lines[:3])
                return f"```\n{preview}\n... ({len(lines) - 3} more lines)\n```"
            else:
                return match.group(0)

        text = re.sub(r"```[\w]*\n(.*?)```", replace_code, text, flags=re.DOTALL)

        return text

    @staticmethod
    def extract_key_info(text: str) -> dict:
        """Extract key information from the content."""
        info = {
            "has_pricing": False,
            "has_api_reference": False,
            "has_quickstart": False,
            "has_examples": False,
            "programming_languages": [],
        }

        text_lower = text.lower()

        # Check for common sections
        info["has_pricing"] = any(
            term in text_lower for term in ["pricing", "cost", "free tier", "billing"]
        )
        info["has_api_reference"] = any(
            term in text_lower for term in ["api reference", "endpoints", "methods"]
        )
        info["has_quickstart"] = any(
            term in text_lower for term in ["quickstart", "getting started", "quick start"]
        )
        info["has_examples"] = "```" in text or "example" in text_lower

        # Detect programming languages
        languages = ["python", "javascript", "typescript", "ruby", "php", "java", "go", "rust", "c#"]
        for lang in languages:
            if lang in text_lower:
                info["programming_languages"].append(lang)

        return info
