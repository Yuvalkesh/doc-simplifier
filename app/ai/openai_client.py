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
        print(f"[DEBUG] OpenAI API key loaded: {api_key[:10]}...")
        # Use shorter timeout for serverless, with retries disabled
        self.client = AsyncOpenAI(
            api_key=api_key,
            timeout=20.0,
            max_retries=0  # Don't retry - serverless timeout is limited
        )
        # Use gpt-4o-mini for faster responses in serverless
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        print(f"[DEBUG] Using model: {self.model}")

    async def generate_report(self, content: str, chunks: list, progress_callback: Optional[Callable] = None) -> dict:
        sections = {}
        truncated = content[:6000]  # Smaller content for faster processing
        # Process sequentially to avoid overwhelming the connection
        for name in SECTION_PROMPTS.keys():
            try:
                sections[name] = await self._gen_section(name, truncated)
            except Exception as e:
                sections[name] = f"😅 Error: {type(e).__name__}: {str(e)[:60]}"
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
