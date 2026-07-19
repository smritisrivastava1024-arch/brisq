"""
app/agents/growth_ai.py
------------------------
Growth strategy agent.
Handles: product ideas, pricing advice, bundles, niche exploration, sales growth strategy.
No Shopify tool calls — pure strategic reasoning.
"""

from app.config import MODEL
from app.deps import groq_client


async def run_growth_ai(user_message: str, history=None) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are Shiftora Growth AI, an e-commerce growth strategist. "
                "Help the owner decide what products to add, how to price products, what bundles to create, "
                "what niches to explore, and how to increase sales.\n\n"
                "Important:\n"
                "- Do NOT call Shopify tools.\n"
                "- Use strategic business reasoning.\n"
                "- If the owner asks for tech product ideas, suggest practical high-margin e-commerce products.\n"
                "- Prefer accessories, consumables, bundles, and lightweight products over low-margin expensive products.\n"
                "- Give clear, actionable recommendations."
            ),
        }
    ]

    if history:
        messages.extend(history[-8:])

    messages.append({"role": "user", "content": user_message})

    response = await groq_client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.4,
    )

    return response.choices[0].message.content
