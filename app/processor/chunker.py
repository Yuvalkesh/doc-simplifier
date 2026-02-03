import re
from typing import List


class DocumentChunker:
    """Split large documents into chunks for API processing."""

    def __init__(self, max_tokens: int = 4000, overlap_tokens: int = 200):
        """
        Initialize chunker.

        Args:
            max_tokens: Maximum tokens per chunk (approximate)
            overlap_tokens: Overlap between chunks for context
        """
        self.max_tokens = max_tokens
        self.overlap_tokens = overlap_tokens
        # Rough approximation: 1 token ~= 4 characters
        self.chars_per_token = 4

    def chunk_document(self, content: str) -> List[str]:
        """
        Split document into chunks.

        Args:
            content: The full document content

        Returns:
            List of content chunks
        """
        # Calculate character limits
        max_chars = self.max_tokens * self.chars_per_token
        overlap_chars = self.overlap_tokens * self.chars_per_token

        # If content fits in one chunk, return as-is
        if len(content) <= max_chars:
            return [content]

        # Try to split by sections first
        chunks = self._split_by_sections(content, max_chars, overlap_chars)

        if chunks:
            return chunks

        # Fallback to paragraph-based splitting
        return self._split_by_paragraphs(content, max_chars, overlap_chars)

    def _split_by_sections(
        self, content: str, max_chars: int, overlap_chars: int
    ) -> List[str]:
        """Split by document sections (headers)."""
        # Split by major headers (# or ##)
        sections = re.split(r"(?=\n#{1,2}\s)", content)

        chunks = []
        current_chunk = ""

        for section in sections:
            if not section.strip():
                continue

            # If adding this section would exceed limit
            if len(current_chunk) + len(section) > max_chars:
                if current_chunk:
                    chunks.append(current_chunk.strip())

                # If single section is too large, split it further
                if len(section) > max_chars:
                    sub_chunks = self._split_by_paragraphs(
                        section, max_chars, overlap_chars
                    )
                    chunks.extend(sub_chunks[:-1])
                    current_chunk = sub_chunks[-1] if sub_chunks else ""
                else:
                    # Start new chunk with some overlap from previous
                    if chunks:
                        # Get last portion of previous chunk for context
                        overlap = current_chunk[-overlap_chars:] if current_chunk else ""
                        current_chunk = overlap + section
                    else:
                        current_chunk = section
            else:
                current_chunk += section

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _split_by_paragraphs(
        self, content: str, max_chars: int, overlap_chars: int
    ) -> List[str]:
        """Split by paragraphs when sections are too large."""
        paragraphs = content.split("\n\n")

        chunks = []
        current_chunk = ""

        for para in paragraphs:
            if not para.strip():
                continue

            if len(current_chunk) + len(para) + 2 > max_chars:
                if current_chunk:
                    chunks.append(current_chunk.strip())

                # Handle very long paragraphs
                if len(para) > max_chars:
                    # Split by sentences as last resort
                    sentences = re.split(r"(?<=[.!?])\s+", para)
                    current_chunk = ""

                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) > max_chars:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = sentence
                        else:
                            current_chunk += " " + sentence if current_chunk else sentence
                else:
                    # Add overlap from previous chunk
                    overlap = current_chunk[-overlap_chars:] if current_chunk else ""
                    current_chunk = overlap + "\n\n" + para
            else:
                current_chunk += "\n\n" + para if current_chunk else para

        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        return len(text) // self.chars_per_token

    def create_context_summary(self, chunks: List[str], index: int) -> str:
        """Create a context summary for a chunk."""
        total = len(chunks)

        if total == 1:
            return ""

        return f"[This is part {index + 1} of {total} of the documentation]\n\n"
