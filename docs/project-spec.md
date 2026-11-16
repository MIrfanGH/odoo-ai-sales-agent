# odoo-ai-sales-agent

## 1. Overview
An AI agent that helps a B2B distributor's sales rep work inside Odoo ERP. The rep asks in plain English, e.g. "Gemini Furniture wants 5 office chairs, can we quote them?" The agent:
1. finds the customer in Odoo
2. checks stock and price for the product
3. drafts a quotation (draft sale.order)
4. replies in plain English

Nothing is written to Odoo until the rep approves.

## 2. Architecture
- **Odoo 18 + PostgreSQL 16**: run with docker-compose at localhost:8069, with demo data.
- **OdooClient**: Python XML-RPC client. Authenticates, reads (search_read) and creates draft sale orders.
- **Tools** (Pydantic-validated args): find_customer, check_stock, create_draft_quotation.
- **Agent loop**: LangChain `create_agent` with gpt-4o-mini. The LLM picks a tool, the result returns as a tool message, repeat until a final answer, capped at 15 steps (`recursion_limit`).
- **FastAPI**: POST /chat with `message` and optional `thread_id`. Returns `thread_id`, `reply`, `awaiting_approval` and `pending_action`. Logging, and a 500 with a clean message on failure.
- **Approval step**: `HumanInTheLoopMiddleware` pauses before `create_draft_quotation`. An in-memory checkpointer (`InMemorySaver`) saves the paused conversation per `thread_id`. The next message on that thread is the decision, parsed in code: "yes" approves, anything else rejects and goes back to the agent as feedback. The approval message is built from the real pending tool arguments.
- **Concurrency**: Odoo calls are serialized with a lock, because the model can run tools in parallel and the XML-RPC connection is not thread-safe.

## 3. Definition of done (all met)
- [x] A multi-step query works end to end: customer, stock, draft quotation, answer (S00030).
- [x] Failure cases are handled: unknown customer, out-of-stock product, ambiguous product name.
- [x] No write to Odoo without approval. Rejecting and changing the quantity writes nothing until the next "yes" (S00031).
- [x] README covers the business use case, setup steps, a sample conversation, and how the agent loop works.

## 4. Out of scope
Custom Odoo modules, UI, authentication, persistent conversation storage, Docker networking and Dockerfiles.

## 5. Next steps
1. Postgres checkpointer so conversations survive a restart and work with several workers.
2. Enforce the out-of-stock rule in the write tool, not only in the prompt.
3. Show customer and product names in the approval message, not only ids.
4. Structured approval endpoint (`/approve`) instead of free-text "yes".
5. Automated tests with a fake model and a stub Odoo client.
6. Several products per quotation, and Odoo pricelists for customer-specific prices.