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
- **Agent loop**: the LLM picks a tool, the result returns as a tool message, repeat until a final answer, capped by a max-iterations limit.
- **FastAPI**: POST /chat, with error handling and logging.
- **Approval step**: the agent proposes the quotation, the user confirms, then it is written.

## 3. Definition of done
- A multi-step query works end to end: customer, stock, draft quotation, answer.
- Failure cases are handled: unknown customer, out-of-stock product, ambiguous product name.
- No write to Odoo without approval.
- README covers the business use case, setup steps, a sample conversation, and how the agent loop works.

## 4. Out of scope
Custom Odoo modules, UI, authentication, Docker networking and Dockerfiles.