import os
import asyncio
from typing import Optional, Callable
from openai import AsyncOpenAI
from dotenv import load_dotenv

from .prompts import SYSTEM_PROMPT, SECTION_PROMPTS

load_dotenv()


class OpenAIClient:
    """Client for OpenAI API interactions."""

    def __init__(self):
        self.client = AsyncOpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            timeout=60.0
        )
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")

    async def generate_report(
        self,
        content: str,
        chunks: list,
        progress_callback: Optional[Callable] = None
    ) -> dict:
        """Generate a fun, simple report."""
        return await self._generate_sections(content, progress_callback)

    async def _generate_sections(
        self,
        content: str,
        progress_callback: Optional[Callable] = None
    ) -> dict:
        """Generate each section."""
        sections = {}
        section_names = list(SECTION_PROMPTS.keys())
        total = len(section_names)

        # Truncate content
        truncated = content[:10000]

        for i, name in enumerate(section_names):
            if progress_callback:
                progress = 50 + int((i / total) * 45)
                emoji_map = {
                    'tldr': '⚡ TL;DR',
                    'superpowers': '💪 Superpowers',
                    'quick_start': '🏁 Quick Start',
                    'video_magic': '🎬 Video Magic',
                    'viral_features': '🔥 Viral Features',
                    'money_talk': '💰 Costs',
                    'watch_out': '⚠️ Watch Out',
                    'ship_today': '🚀 Ship Today'
                }
                await progress_callback(progress, f"Writing {emoji_map.get(name, name)}...")

            try:
                response = await asyncio.wait_for(
                    self.client.chat.completions.create(
                        model=self.model,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": f"API Docs:\n{truncated}\n\n---\n{SECTION_PROMPTS[name]}"}
                        ],
                        temperature=0.8,
                        max_tokens=600
                    ),
                    timeout=30.0
                )
                sections[name] = response.choices[0].message.content.strip()
                print(f"✓ {name}")
            except asyncio.TimeoutError:
                sections[name] = "⏱️ This section took too long. Try refreshing!"
            except Exception as e:
                sections[name] = f"😅 Oops! Something went wrong: {str(e)[:50]}"

            await asyncio.sleep(0.1)

        return sections
