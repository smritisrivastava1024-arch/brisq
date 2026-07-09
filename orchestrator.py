"""
orchestrator.py
----------------
Routes messages to the correct Shiftora specialist agent.

Agents:
- customer_ai   -> customer support: orders, refunds, returns, product availability, policies
- operations_ai -> inventory, reordering, stock overview, fulfillment operations
- finance_ai    -> revenue, P&L, bookkeeping, cash flow, refund risk, refund approvals
- growth_ai     -> product ideas, pricing, bundles, marketing, sales growth strategy
- executive_ai  -> daily briefings, business summaries, strategic recommendations
- supplier_ai   -> purchase orders, supplier follow-up, supplier communication

This file is synchronous because your existing agent functions are synchronous.
"""

import json


CLASSIFIER_SYSTEM_PROMPT = """You are the routing classifier for Shiftora, an AI operations platform for e-commerce businesses.

Your job is to decide which specialist AI agent(s) should answer the user's message.

Available agents:

1. "customer_ai"
Use for:
- order status
- order tracking
- where is my order
- refund eligibility
- return questions
- shipping policy
- warranty policy
- cancellation policy
- product availability for customers
- customer support questions

2. "operations_ai"
Use for:
- inventory overview
- stock overview
- low-stock products
- what needs reordering
- fastest sellers
- demand forecasting
- when will a product run out
- fulfillment operations
- unfulfilled orders
- operational bottlenecks

3. "finance_ai"
Use for:
- revenue
- sales totals
- earnings
- profit and loss
- P&L
- bookkeeping
- journal entries
- taxes
- refunds summary
- refund risk analysis
- chargeback risk
- cash flow
- profit forecast
- create refund approval
- approve/reject refund workflow
- financial reports

4. "growth_ai"
Use for:
- what product should I add
- product ideas
- what should I sell
- trending products
- pricing advice
- product bundles
- marketing ideas
- ad copy strategy
- sales growth strategy
- niche ideas
- tech product suggestions
- how to increase sales

IMPORTANT:
If the user asks what products to add, what niche to sell, or says they are interested in a category like "tech",
route to "growth_ai", NOT inventory or operations.

5. "executive_ai"
Use for:
- daily briefing
- weekly business summary
- executive summary
- what should I focus on today
- overall business health
- summarize everything
- CEO-style recommendations
- strategic overview

6. "supplier_ai"
Use for:
- supplier emails
- purchase orders
- supplier follow-up
- vendor communication
- reorder email
- supplier pricing comparison
- delayed shipment follow-up

Rules:
- A message can require multiple agents.
- Customer-facing refund eligibility goes to customer_ai.
- Owner-facing refund risk, approval, chargeback, or financial refund analysis goes to finance_ai.
- Inventory data and stockouts go to operations_ai.
- Product launch ideas and sales strategy go to growth_ai.
- High-level business summaries go to executive_ai.
- Supplier communication goes to supplier_ai.

Return ONLY valid JSON in this exact format:
{"agents": ["finance_ai"]}

or:
{"agents": ["operations_ai", "finance_ai"]}

If the message is only a greeting or too vague, return:
{"agents": []}

7. "marketing_ai"
Use for:
- product descriptions
- SEO titles
- SEO meta descriptions
- ad copy
- Facebook ads
- Google ads
- Instagram captions
- email campaigns
- product launch plans
- seasonal campaigns
- abandoned cart recovery messages
- marketing content
"""


def _build_classifier_user_prompt(message, history=None):
    """
    Builds a context-aware classification prompt.
    This helps with short follow-ups like:
    User: "What products should I add?"
    User: "tech"
    """
    history_text = ""

    if history:
        recent = history[-8:]
        formatted = []

        for item in recent:
            role = item.get("role", "user")
            content = item.get("content", "")
            formatted.append(f"{role}: {content}")

        history_text = "\n".join(formatted)

    return f"""Conversation history:
{history_text}

Current user message:
{message}

Classify the current user message using the available Shiftora agents.
Return only JSON."""


def classify_intent(message, client, model, history=None):
    """
    Ask the LLM which agent(s) should handle this message.
    """
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
            {"role": "user", "content": _build_classifier_user_prompt(message, history)},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content

    try:
        parsed = json.loads(raw)
        agents = parsed.get("agents", [])

        valid_agents = {
            "customer_ai",
            "operations_ai",
            "finance_ai",
            "growth_ai",
            "executive_ai",
            "supplier_ai",
            "marketing_ai",
        }

        return [agent for agent in agents if agent in valid_agents]

    except (json.JSONDecodeError, AttributeError, TypeError):
        return []


def route_message(message, client, model, agent_functions, history=None):
    """
    Routes a user message to one or more specialist agents.

    agent_functions example:

    agent_functions = {
        "customer_ai": run_customer_ai,
        "operations_ai": run_operations_ai,
        "finance_ai": run_finance_ai,
        "growth_ai": run_growth_ai,
        "executive_ai": run_executive_ai,
        "supplier_ai": run_supplier_ai,
    }
    """
    agents_needed = classify_intent(message, client, model, history)

    if not agents_needed:
        return {
            "agents_used": [],
            "reply": (
                "Hi! I can help with customer support, inventory, finance, growth strategy, "
                "supplier operations, or executive business summaries. What would you like to do?"
            ),
        }

    results = []

    for agent_name in agents_needed:
        if agent_name not in agent_functions:
            results.append(
                (
                    agent_name,
                    f"{agent_name} is not available in this chat mode."
                )
            )
            continue

        try:
            agent_fn = agent_functions[agent_name]
            answer = agent_fn(message)
            results.append((agent_name, answer))

        except Exception as error:
            results.append(
                (
                    agent_name,
                    f"{agent_name} encountered an error: {str(error)}"
                )
            )

    if len(results) == 1:
        combined_reply = results[0][1]
    else:
        combined_reply = merge_answers(message, results, client, model)

    return {
        "agents_used": agents_needed,
        "reply": combined_reply,
    }


def merge_answers(original_message, results, client, model):
    """
    When multiple agents answer, merge them into one clean response.
    """
    sources_text = "\n\n".join(
        f"[{agent_name.upper()} SAID]:\n{answer}"
        for agent_name, answer in results
    )

    merge_prompt = f"""The user asked:

"{original_message}"

Multiple Shiftora specialist agents answered. Their raw answers are below:

{sources_text}

Write ONE clear, useful, non-repetitive response.

Rules:
- Do not mention internal agent names.
- Do not invent facts.
- If an agent says an order was not found, do NOT invent refund approvals or refund amounts.
- If financial numbers are provided, preserve them exactly.
- If there are recommendations, organize them clearly.
- Keep the answer practical for a business owner.
"""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": merge_prompt}],
        temperature=0,
    )

    return response.choices[0].message.content