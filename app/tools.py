"""LangChain tools that the agent can call. Thin wrappers around OdooClient.

Each tool: validates input (Pydantic), calls Odoo, and returns plain text the
LLM can read. Odoo errors are returned as text instead of raised, so the agent
can explain the problem to the user instead of crashing.
"""
import logging
import threading
from functools import lru_cache

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from app.odoo_client import OdooClient, OdooError

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _client() -> OdooClient:
    """One shared Odoo connection, created on first use."""
    return OdooClient()


# The Odoo connection (xmlrpc) is not thread-safe, and the agent can run several
# tools in parallel. This lock makes Odoo calls go one at a time.
_odoo_lock = threading.Lock()


class FindCustomerArgs(BaseModel):
    name: str = Field(description="Full or partial customer company name, e.g. 'Gemini'.")


class CheckStockArgs(BaseModel):
    product_name: str = Field(description="Full or partial product name, e.g. 'Office Chair'.")


class CreateDraftQuotationArgs(BaseModel):
    partner_id: int = Field(description="Customer id, taken from find_customer.")
    product_id: int = Field(description="Product id, taken from check_stock.")
    qty: int = Field(gt=0, description="Quantity to quote. Must be greater than 0.")


@tool("find_customer", args_schema=FindCustomerArgs)
def find_customer(name: str) -> str:
    """Search Odoo for customers by name. Returns id, name and email of each match.
    Call this first to get the customer id needed for a quotation."""
    try:
        with _odoo_lock:
            rows = _client().find_customer(name)
    except OdooError as e:
        logger.warning("find_customer failed: %s", e)
        return f"Odoo error while searching customers: {e}"
    if not rows:
        return f"No customer found matching '{name}'."
    return "\n".join(f"id={r['id']} | {r['name']} | {r.get('email') or 'no email'}" for r in rows)


@tool("check_stock", args_schema=CheckStockArgs)
def check_stock(product_name: str) -> str:
    """Search Odoo products by name. Returns id, units in stock and unit price of each match.
    Use it to check availability and to get the product id needed for a quotation."""
    try:
        with _odoo_lock:
            rows = _client().check_stock(product_name)
    except OdooError as e:
        logger.warning("check_stock failed: %s", e)
        return f"Odoo error while checking stock: {e}"
    if not rows:
        return f"No product found matching '{product_name}'."
    lines = []
    for r in rows:
        stock = f"{r['qty_available']:g} in stock" if r["qty_available"] > 0 else "OUT OF STOCK"
        lines.append(f"id={r['id']} | {r['name']} | {stock} | unit price {r['list_price']:g}")
    return "\n".join(lines)


@tool("create_draft_quotation", args_schema=CreateDraftQuotationArgs)
def create_draft_quotation(partner_id: int, product_id: int, qty: int) -> str:
    """Create a DRAFT sales quotation in Odoo with one product line.
    Only call after find_customer and check_stock, and only once the user has confirmed
    the customer, product and quantity. This writes to Odoo."""
    try:
        with _odoo_lock:
            q = _client().create_draft_quotation(partner_id, product_id, qty)
    except (OdooError, ValueError) as e:
        logger.warning("create_draft_quotation failed: %s", e)
        return f"Could not create the quotation: {e}"
    return f"Draft quotation {q['name']} created. Total: {q['amount_total']:g}. Status: {q['state']}."


TOOLS = [find_customer, check_stock, create_draft_quotation]