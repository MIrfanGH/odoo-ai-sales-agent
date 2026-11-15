# odoo-ai-sales-agent

An AI sales assistant for Odoo 18. A sales rep asks in plain English, and the agent finds the customer, checks stock and price, and creates a draft quotation through Odoo's API, only after approval.

Business context: [docs/business-overview.md](docs/business-overview.md)

Technical spec: [docs/project-spec.md](docs/project-spec.md)

**Status:** Odoo client working (find customer, check stock, create draft quotation). Agent, approval step and `/chat` endpoint in progress.

## Stack

Python, Odoo 18, PostgreSQL 16, Docker Compose, XML-RPC. Coming next: LangChain, FastAPI, OpenAI.

## Setup

1. Start Odoo and Postgres:
   ```
   docker compose up -d
   ```
2. Open http://localhost:8069, create a database (e.g. `odoo_sales`) with demo data, and install Sales and Inventory.
3. Copy `.env.example` to `.env` and fill in your Odoo database name, login email and password.
4. Install dependencies and run the client:
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   python -m app.odoo_client
   ```

Expected output: a customer, matching products with stock and price, and a new draft quotation (e.g. `S00025`).