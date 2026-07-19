"""
app/agents/supplier_ai.py
--------------------------
Supplier communications agent.
Handles: supplier emails, purchase order drafts, reorder messages, supplier follow-ups.
All outputs are drafts — never sends emails or places real orders.
"""

from app.config import MODEL
from app.deps import groq_client


async def run_supplier_ai(user_message: str, history=None) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are Shiftora Supplier AI. "
                "Help create supplier emails, purchase order drafts, reorder messages, and supplier follow-ups. "
                "Do not actually send emails or place purchase orders. "
                "Always frame supplier actions as drafts for owner approval."
            ),
        }
    ]

    if history:
        messages.extend(history[-8:])

    messages.append({"role": "user", "content": user_message})

    response = await groq_client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0.3,
    )

    return response.choices[0].message.content
