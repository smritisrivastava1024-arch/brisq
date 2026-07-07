"""
orchestrator.py
----------------
Routes an incoming customer message to one or more of your existing
agent functions (run_support_agent, run_inventory_agent, run_policy_agent)
and merges their responses into a single reply.

This matches your actual api.py -- your agent functions are synchronous,
so this orchestrator is synchronous too (no asyncio rewrite needed).

USAGE: drop this file next to api.py, then add the import + endpoint
shown at the bottom of this file into api.py.
"""

import json


CLASSIFIER_SYSTEM_PROMPT = """You are a routing classifier for an e-commerce AI support system.

Given a customer message, decide which specialist agent(s) are needed to answer it.

Available agents:
- "support"     -> order status, refunds, order tracking, "where is my order"
- "inventory"   -> ONE specific product availability, "do you have X in stock", "is X available"
- "policy"      -> return policy, refund policy, shipping policy, warranty, damaged items, cancellations
- "forecasting" -> stock overview of ALL products, reorder needs, sales velocity, demand prediction, "what needs reordering", "stock overview", "fastest sellers", "when will X run out", "should I restock"
- "finance"     -> revenue, sales totals, earnings, best selling products, refund rate, financial summaries, "how much did we make", "top products", "weekly sales", "monthly revenue"

IMPORTANT: "stock overview", "all products", "what needs reordering", "fastest sellers" → ALWAYS route to "forecasting", NOT "inventory".
"inventory" is ONLY for questions about one specific named product.
"finance" is for revenue/earnings questions, NOT inventory questions.

A message can need MORE THAN ONE agent (e.g. "where's my order and can I return it?"
needs both "support" and "policy").

Respond with ONLY valid JSON in this exact format, nothing else:
{"agents": ["support"]}

or

{"agents": ["support", "policy"]}

If the message is just small talk / greeting and matches none of the agents, respond:
{"agents": []}
"""


def classify_intent(message, client, model):
    """Ask the LLM which agent(s) should handle this message."""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": CLASSIFIER_SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content

    try:
        parsed = json.loads(raw)
        agents = parsed.get("agents", [])
        valid = {"support", "inventory", "policy", "forecasting", "finance"}
        return [a for a in agents if a in valid]
    except (json.JSONDecodeError, AttributeError):
        return []


def route_message(message, client, model, agent_functions):
    """
    agent_functions is a dict mapping agent name -> function, e.g.:

        agent_functions = {
            "support": run_support_agent,
            "inventory": run_inventory_agent,
            "policy": run_policy_agent,
        }

    Each function takes a single string argument (the user message)
    and returns a string answer -- exactly like your existing functions.
    """
    agents_needed = classify_intent(message, client, model)

    if not agents_needed:
        return {
            "agents_used": [],
            "reply": (
                "Hi! I can help with order status, refunds, product "
                "availability, or store policies. Could you tell me a "
                "bit more about what you need?"
            ),
        }

    results = []
    for name in agents_needed:
        agent_fn = agent_functions[name]
        answer = agent_fn(message)
        results.append((name, answer))

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
    When more than one agent answered, ask the LLM to write ONE clean,
    non-repetitive reply using their raw answers as source material --
    instead of just gluing the answers together with newlines.
    """
    sources_text = "\n\n".join(
        f"[{name.upper()} AGENT SAID]: {answer}" for name, answer in results
    )

    merge_prompt = f"""A customer asked: "{original_message}"

Multiple specialist agents each answered part of this question. Their raw answers are below.

{sources_text}

Write ONE clear, friendly, non-repetitive reply to the customer that combines
only the relevant facts from the agents above. Do not repeat the same fact twice.
Do not mention "agents" or that multiple systems were involved -- just answer
naturally as a single support assistant. Do not invent any facts that weren't
in the agents' answers above."""

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": merge_prompt}],
        temperature=0,
    )
    return response.choices[0].message.content


# ----------------------------------------------------------------------
# Add this to your api.py (near the bottom, with the other endpoints)
# ----------------------------------------------------------------------
#
# from orchestrator import route_message
#
# @app.post("/chat")
# def chat_endpoint(request: ChatRequest):
#     agent_functions = {
#         "support": run_support_agent,
#         "inventory": run_inventory_agent,
#         "policy": run_policy_agent,
#         "forecasting": run_forecasting_agent,
#     }
#     result = route_message(request.message, client, MODEL, agent_functions)
#     return result
#
# That's it -- no other changes needed. Your existing /support, /inventory,
# and /policy endpoints can stay as they are (useful for testing each
# agent directly), and /chat becomes the new single entry point for
# chat.html to call.
#
# In chat.html, change the fetch URL from whichever endpoint it currently
# calls to:
#
#     fetch("http://127.0.0.1:8000/chat", { ... })
#
# and you're done.