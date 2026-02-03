import os
import asyncio
from typing import Optional, Callable
from openai import AsyncOpenAI
from dotenv import load_dotenv
from .prompts import SYSTEM_PROMPT, SECTION_PROMPTS

load_dotenv()

class OpenAIClient:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        # Log key prefix for debugging (safe - only shows first chars)
        print(f"[DEBUG] OpenAI API key loaded: {api_key[:10]}...")
        self.client = AsyncOpenAI(api_key=api_key, timeout=30.0)
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
        print(f"[DEBUG] Using model: {self.model}")

    async def generate_report(self, content: str, chunks: list, progress_callback: Optional[Callable] = None) -> dict:
        sections = {}
        truncated = content[:8000]
        tasks = [self._gen_section(name, truncated) for name in SECTION_PROMPTS.keys()]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for name, result in zip(SECTION_PROMPTS.keys(), results):
            sections[name] = result if not isinstance(result, Exception) else f"😅 Error: {str(result)[:80]}"
        return sections

    async def _gen_section(self, name: str, content: str) -> str:
        try:
            r = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Docs:\n{content}\n\n---\n{SECTION_PROMPTS[name]}"}
                    ],
                    temperature=0.7, max_tokens=500
                ), timeout=55.0)
            return r.choices[0].message.content.strip()
        except asyncio.TimeoutError:
            return "⏱️ Timed out"
        except Exception as e:
            return f"⚠️ {type(e).__name__}: {str(e)[:100]}"
