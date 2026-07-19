import re

with open('orchestrator.py', 'r') as f:
    content = f.read()

# 1. async defs
funcs = ['classify_intent', 'route_message', 'merge_answers']
for func in funcs:
    content = re.sub(fr'^def {func}\(', f'async def {func}(', content, flags=re.MULTILINE)

# 2. client.chat.completions.create
content = content.replace('client.chat.completions.create', 'await client.chat.completions.create')

# 3. await agent_fn
content = content.replace('answer = agent_fn(message)', 'answer = await agent_fn(message)')

# 4. await classify_intent
content = content.replace('classify_intent(message, client, model, history)', 'await classify_intent(message, client, model, history)')

# 5. await merge_answers
content = content.replace('merge_answers(message, results, client, model)', 'await merge_answers(message, results, client, model)')

with open('orchestrator.py', 'w') as f:
    f.write(content)

print("orchestrator.py refactored.")
