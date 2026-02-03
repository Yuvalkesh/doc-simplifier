"""Prompts for simplifying ANY documentation for non-technical readers."""

SYSTEM_PROMPT = """You're a friendly expert who explains technical documentation to non-technical people.

Your style:
- Write like you're explaining to a smart friend who doesn't code
- Use emojis to make it fun and scannable 🎯
- Short sentences. Simple words. No jargon.
- Focus on WHAT you can DO, not how it works technically
- Be encouraging and practical
- Use bullet points and numbered lists"""

SECTION_PROMPTS = {
    "tldr": """Give me a 2-3 sentence summary of what this tool/API/service does.
Use emojis. Make it exciting and clear. Like explaining to a friend at coffee.""",

    "superpowers": """List 5-6 awesome things you can DO or BUILD with this.
Format each like:
🎯 **Cool thing** - one sentence explaining why it's useful

Be specific and exciting! Focus on real benefits.""",

    "quick_start": """Write the simplest "get started" steps (3-5 max).
Format:
1️⃣ **First step** - what to do
2️⃣ **Second step** - what to do

Assume the reader is smart but not technical. Include links to signup if mentioned.""",

    "video_magic": """Give 3-4 real-world examples of how people actually use this.
Format:
💡 **Use case** - brief explanation

Think: What problems does this solve? Who benefits?""",

    "viral_features": """What are the BEST features that make this tool special?
List 4-5 standout features:
✨ **Feature** - why it's great

Focus on what makes users say "wow".""",

    "money_talk": """Break down the pricing simply:
💰 **Free tier** - what you get for free
💳 **Paid plans** - what they cost and include
⚠️ **Watch out** - any hidden costs or limits

If pricing isn't mentioned, say "Check their website for current pricing.""",

    "watch_out": """What are 3-4 things to be careful about?
Format:
⚠️ **Gotcha** - how to handle it

Be helpful, not scary. Include workarounds.""",

    "ship_today": """What's ONE simple thing someone could try TODAY?
Format:
🚀 **Try this:** [specific action]
- Step 1
- Step 2
- Step 3

Make it achievable in under an hour."""
}

COMBINE_PROMPT = """Combine these notes into one clean section. Keep emojis and simple language.
{chunk_analyses}
Write the combined {section_name}:"""
