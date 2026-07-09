"""
marketing_ai.py
----------------
Marketing AI module for Brisq.

Handles:
- Product descriptions
- SEO content
- Ads
- Email campaigns
- Instagram captions
- Launch plans
- Bundle ideas
- Seasonal campaigns
"""
from shopify_tools import get_abandoned_checkouts


def run_marketing_ai(user_message, client, model, history=None):
    lower_message = user_message.lower()

    # If owner asks about abandoned carts, fetch real Shopify abandoned checkouts first
    if (
        "abandoned cart" in lower_message
        or "abandoned checkout" in lower_message
        or "recover cart" in lower_message
        or "cart recovery" in lower_message
    ):
        abandoned_data = get_abandoned_checkouts(days=7)

        prompt = f"""
You are Brisq Marketing AI.

The owner asked:
{user_message}

Here is the real Shopify abandoned checkout data:
{abandoned_data}

Create an abandoned cart recovery plan.

Return:
1. Summary of abandoned carts
2. Email recovery message
3. WhatsApp recovery message
4. Suggested incentive
5. Recommended send timing
6. Owner approval note

Important:
- Do not say messages were sent.
- Do not claim recovery happened.
- These are drafts only.
- Owner must approve before sending.
"""

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )

        return response.choices[0].message.content

    # Normal marketing generation
    messages = [
        {
            "role": "system",
            "content": (
                "You are Brisq Marketing AI for e-commerce businesses. "
                "You help store owners create high-converting marketing content. "
                "You can generate product descriptions, SEO titles, ads, emails, "
                "Instagram captions, product launch plans, bundle ideas, and seasonal campaigns. "
                "Be practical, business-focused, and conversion-oriented. "
                "Do not invent fake sales data. If the user gives product details, use them. "
                "If details are missing, make reasonable assumptions and clearly say they can customize them."
            )
        }
    ]

    if history:
        messages.extend(history[-8:])

    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.5
    )

    return response.choices[0].message.content