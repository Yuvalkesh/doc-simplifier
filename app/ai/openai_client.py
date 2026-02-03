import os
import httpx
from typing import Optional, Callable
from dotenv import load_dotenv
from .prompts import SYSTEM_PROMPT, SECTION_PROMPTS

load_dotenv()

class OpenAIClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        print(f"[DEBUG] OpenAI API key loaded: {self.api_key[:10]}...")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        print(f"[DEBUG] Using model: {self.model}")
        self.api_url = "https://api.openai.com/v1/chat/completions"

    async def generate_report(self, content: str, chunks: list, progress_callback: Optional[Callable] = None) -> dict:
        sections = {}
        truncated = content[:6000]
        for name in SECTION_PROMPTS.keys():
            try:
                sections[name] = await self._gen_section(name, truncated)
            except Exception as e:
                sections[name] = f"😅 Error: {type(e).__name__}: {str(e)[:60]}"
        return sections

    async def _gen_section(self, name: str, content: str) -> str:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": f"Docs:\n{content}\n\n---\n{SECTION_PROMPTS[name]}"}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 500
                    }
                )
                if response.status_code != 200:
                    return f"⚠️ API Error {response.status_code}: {response.text[:80]}"
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
        except httpx.TimeoutException:
            return "⏱️ Timed out"
        except Exception as e:
            return f"⚠️ {type(e).__name__}: {str(e)[:100]}"
