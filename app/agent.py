"""The sales agent: 
                model + tools + system prompt + approval gate + memory."""

from langchain.agents import create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver

from app.tools import TOOLS

MODEL = "openai:gpt-4o-mini"

SYSTEM_PROMPT = """You are a B2B sales assistant for a distributor, working inside Odoo.

To prepare a quotation: 1) find_customer, 2) check_stock, 3) create_draft_quotation.

Rules:
- If a customer or product name matches several records, list the options and ask which one. Never guess.
- If no customer or product is found, say so and stop. Never invent ids.
- If stock is 0 or below the requested quantity, say so clearly and ask how to proceed. Do not create the quotation.
- Before create_draft_quotation, write one line with customer, product, quantity and total price. The user will then be asked to approve. Never say a quotation exists until the tool confirms it.
- Use only data returned by the tools. Keep answers short."""


def build_agent(model=MODEL):
    return create_agent(
        model=model,
        tools=TOOLS,
        system_prompt=SYSTEM_PROMPT,
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={
                    "create_draft_quotation": {"allowed_decisions": ["approve", "reject"]},
                    "find_customer": False,
                    "check_stock": False,
                },
            )
        ],
        checkpointer=InMemorySaver(),  # stores each conversation, needed to pause and resume
    )