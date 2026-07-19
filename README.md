# E-commerce AI Agent System

A multi-agent backend system that automates customer support, inventory queries, and policy questions for e-commerce businesses using LLM-powered tool calling, retrieval-augmented generation (RAG), and concurrent request handling.

## What it does

Online stores spend significant time on repetitive operational tasks — order tracking, refund eligibility checks, stock lookups, and answering policy questions. This system automates all three using specialized AI agents that query real data instead of guessing or hallucinating answers.

## Architecture

```
                        ┌─────────────────┐
                        │   Chat UI        │
                        │   (chat.html)    │
                        └────────┬─────────┘
                                 │ HTTP
                        ┌────────▼─────────┐
                        │   FastAPI Server  │
                        │     (api.py)      │
                        └────────┬─────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            │                    │                     │
    ┌───────▼───────┐   ┌────────▼────────┐   ┌────────▼────────┐
    │ Support Agent  │   │ Inventory Agent │   │  Policy Agent   │
    │  (tool calling)│   │  (tool calling) │   │     (RAG)       │
    └───────┬───────┘   └────────┬────────┘   └────────┬────────┘
            │                    │                     │
    ┌───────▼────────────────────▼───────┐   ┌─────────▼─────────┐
    │         SQLite (store.db)           │   │  ChromaDB vector   │
    │   orders · refunds · inventory      │   │  store (policies)  │
    └──────────────────────────────────────┘   └─────────────────────┘
```

Each agent is powered by an LLM (Groq's `llama-3.3-70b-versatile`) and uses **function/tool calling** to decide when it needs to query real data versus answering directly — the model is never allowed to invent order details, stock numbers, or policy facts.

## Agents

**Support Agent** — looks up order status and refund eligibility from a SQLite database. Handles queries like "Where is my order #1234?" or "Can I get a refund for order #9999?"

**Inventory Agent** — checks stock levels and warehouse location for products. Handles queries like "Do you have Running Shoes in stock?"

**Policy Agent** — uses retrieval-augmented generation (RAG) over real store policy documents (return, refund, shipping, cancellation, warranty, damaged item policies). Instead of hardcoding every possible policy answer, it embeds policy text into a vector database (ChromaDB) and retrieves the most relevant section to answer questions like "Can I return a sale item?" or "What if my item arrives damaged?"

## Key technical features

- **Tool calling** — agents autonomously decide when to query a database versus answering directly, rather than always running a fixed lookup
- **Concurrency** — multiple customer requests are processed simultaneously using Python's `asyncio` with a thread pool executor, rather than sequentially
- **RAG pipeline** — policy documents are chunked, embedded using `sentence-transformers`, stored in ChromaDB, and retrieved by semantic similarity at query time
- **Persistent storage** — order, refund, and inventory data is stored in a real SQLite database rather than in-memory structures
- **REST API** — all three agents are exposed as independent HTTP endpoints via FastAPI, making the system callable from any frontend or service
- **Hallucination guarding** — strict system instructions and `temperature=0` on final responses ensure agents only state facts returned by their tools

## Tech stack

- **Language:** Python
- **LLM:** Groq API (`llama-3.3-70b-versatile`)
- **Web framework:** FastAPI + Uvicorn
- **Database:** SQLite
- **Vector store:** ChromaDB with `sentence-transformers` embeddings
- **Concurrency:** `asyncio`
- **Frontend:** React + Vite + Tailwind v4 (TypeScript)

## Setup

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Configure environment variables**

Copy the example env file and fill in your real values:
```bash
cp .env.example .env
```

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | API key from [console.groq.com](https://console.groq.com) |
| `OWNER_PASSWORD` | Password for owner-facing dashboard endpoints |
| `SHOPIFY_STORE_URL` | Your store domain, e.g. `my-store.myshopify.com` |
| `SHOPIFY_ACCESS_TOKEN` | Shopify Admin API private/custom app token |

> **Note:** `.env` is gitignored. Never commit it. The `.env.example` file (safe to commit) lists every required key with placeholder values.

**3. Generate local databases and vector store**

`brisq.db`, `store.db`, and `chroma_db/` are **gitignored** — they live only on your local machine and are never committed to the repo. Regenerate them by running:

```bash
python setup_db.py            # creates store.db with sample orders/inventory
python setup_sales_history.py # populates sales_history table in store.db
python setup_rag.py           # creates chroma_db/ vector store from policies.txt
```

Re-run these scripts any time you need to reset to a clean state.

**4. Start the API server**

**Option A: Using Docker (Recommended for Deployment)**
```bash
docker compose up --build
```
This spins up the FastAPI app inside a container, mapping port 8000. It uses local volumes to persist your `brisq.db` and `chroma_db/` across container restarts.

**Option B: Running Locally (Manual)**
```bash
uvicorn app.main:app --reload
```

**5. Start the frontend**

The web interface has been rewritten in React. To start it:

```bash
cd frontend
npm install
npm run dev
```

Then visit `http://localhost:5173` for the customer chat, and `http://localhost:5173/owner/login` for the owner dashboard.

## API endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/support` | POST | Order status and refund queries |
| `/inventory` | POST | Stock level queries |
| `/policy` | POST | Store policy questions (RAG) |

Example request:
```bash
curl -X POST http://127.0.0.1:8000/support \
  -H "Content-Type: application/json" \
  -d '{"message": "Where is my order #1234?"}'
```

Interactive API documentation is available at `http://127.0.0.1:8000/docs` once the server is running.

## Sample data

The system ships with sample data for demonstration:
- 3 sample orders (`1234`, `5678`, `9999`)
- 3 inventory items (Wireless Headphones, Running Shoes, Phone Case)
- 6 policy categories (return, refund, shipping, cancellation, warranty, damaged item)

## Future improvements

- Replace sample SQLite data with a real e-commerce platform integration (Shopify/WooCommerce API)
- Add a router/orchestrator agent to automatically classify and route incoming queries to the correct specialist agent
- Add a message queue (Celery + Redis) for handling request bursts at scale
- Add structured logging and a metrics dashboard for response time and tool-call success rate

## Author

Built by Smriti Srivastava as a learning project exploring agentic AI systems, concurrent backend architecture, and retrieval-augmented generation.