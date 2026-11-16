# odoo-ai-sales-agent

An AI sales assistant for Odoo 18. A sales rep asks in plain English, and the agent finds the customer, checks stock and price, and creates a draft quotation through Odoo's API, only after the rep approves.

Business context: [docs/business-overview.md](docs/business-overview.md)

Technical spec: [docs/project-spec.md](docs/project-spec.md)

**Status:** Working end to end. Tested manually through `/docs`: happy path, unknown customer, ambiguous product, out of stock, and reject-then-change.

## Stack

Python, LangChain (`create_agent`, human-in-the-loop middleware), LangGraph, OpenAI gpt-4o-mini, FastAPI, Odoo 18 (XML-RPC), PostgreSQL 16, Docker Compose.

## How it works

```
POST /chat (message, thread_id)
  -> agent (LLM decides the next step)
       -> find_customer   (read, runs freely)
       -> check_stock     (read, runs freely)
       -> create_draft_quotation (write, PAUSES for approval)
  -> OdooClient (XML-RPC) -> Odoo 18
```

- The agent calls tools in a loop until it has an answer, with a 15-step limit.
- Before the write tool runs, the agent pauses. The conversation is saved under its `thread_id`, and the response has `awaiting_approval: true` and the exact tool arguments.
- The next message on the same thread is the decision: "yes" approves, and anything else rejects and goes back to the agent as feedback (for example "no, make it 3 instead"). The decision is made in code, not by the LLM.

## Setup

1. Start Odoo and Postgres:
   ```
   docker compose up -d
   ```
2. Open http://localhost:8069, create a database (e.g. `odoo_sales`) with demo data, and install Sales and Inventory.
3. Copy `.env.example` to `.env` and fill in ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD and OPENAI_API_KEY.
4. Install and run:
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload
   ```
5. Open http://localhost:8000/docs and use `POST /chat`. Leave out `thread_id` to start a new conversation, and send the returned `thread_id` on follow-ups.

To test the Odoo client alone: `python -m app.odoo_client`

## Sample conversation (real run, agent replies shortened)

```
Rep:    Quote 5 Office Chair for Gemini Furniture
Agent:  Found Gemini Furniture (ID 11). Two products match:
        1. Office Chair (ID 5), 20 in stock, unit price 70
        2. Office Chair Black (ID 25), 10 in stock, unit price 120.5
        Which product?
Rep:    office chair, id 5
Agent:  Ready to create draft quotation: customer id 11, product id 5, qty 5.
        Approval needed. Reply 'yes' to create it, or tell me what to change.
        (awaiting_approval: true, nothing written yet)
Rep:    yes
Agent:  Draft quotation S00030 created for Gemini Furniture, Office Chair, quantity 5, total 350.
```

Reject and change (real run):

```
Agent:  Ready to create draft quotation: customer id 11, product id 5, qty 5. Approval needed.
Rep:    no, make it 3 instead
Agent:  Ready to create draft quotation: customer id 11, product id 5, qty 3. Approval needed.
        (nothing written)
Rep:    yes
Agent:  Draft quotation created: Office Chair, quantity 3, total 210.   (S00031)
```

Other cases:
- `Quote 2 chairs for Acme Corp`: "No customer found matching Acme Corp."
- `Quote 3 Office Lamps for Gemini Furniture`: "Office Lamp is out of stock (0 units). How would you like to proceed?" No approval is requested.

## Agent loop: manual vs LangChain

In ai-customer-support-agent I wrote the tool calling by hand: one model call, run the tool, send the result back. Here `create_agent` runs the whole loop. The model picks a tool, LangChain runs it and adds the result as a tool message, and the model is called again until it gives a final answer. LangChain also generates the tool schemas from the Pydantic models, runs several tool calls in parallel, and limits the number of steps. `HumanInTheLoopMiddleware` adds the pause before the write tool, and the checkpointer saves the paused conversation so it can resume on the next HTTP request.

## Design decisions

- **Approval in code, not in the prompt:** the write tool can't run without an explicit "yes", whatever the model says.
- **Approval message from real arguments:** the user sees the actual customer id, product id and quantity that will be written, not the model's own description.
- **Odoo errors returned as text:** the agent explains the problem instead of crashing.
- **Lock around Odoo calls:** the model can call two tools at once, and LangGraph runs them in parallel threads. The shared XML-RPC connection allows one request at a time, so the calls are serialized. This was found in testing as a `CannotSendRequest` crash.

## Known limitations

- Conversations are kept in memory: they are lost on restart and don't work with several workers. A Postgres checkpointer would fix this.
- No authentication, and the client chooses `thread_id`.
- The out-of-stock rule is enforced by the prompt, not in code.
- Approval is free text: "yes" works, but "yes please" counts as a rejection.
- The approval message shows customer and product ids, not names.
- An unexpected error inside a tool (anything other than an Odoo error) returns a 500, and that conversation can't be continued; start a new one.
- One quotation line per request. No pricelists or discounts.

## Files

- `app/config.py` loads settings from `.env` and fails fast if one is missing
- `app/odoo_client.py` Odoo XML-RPC client
- `app/tools.py` 3 LangChain tools wrapping it
- `app/agent.py` model, system prompt, approval gate, conversation memory
- `app/main.py` FastAPI `/chat` endpoint