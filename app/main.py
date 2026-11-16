"""FastAPI entry point. POST /chat talks to the agent.

Approval flow: when the agent wants to create a quotation it pauses. The next
message on the same thread_id is read as the decision: "yes" approves, anything
else rejects and is passed back to the agent as feedback.
"""
import logging
import uuid

from fastapi import FastAPI, HTTPException
from langgraph.errors import GraphRecursionError
from langgraph.types import Command
from pydantic import BaseModel, Field

from app.agent import build_agent

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("app.main")

MAX_STEPS = 15  # hard limit on agent loop steps per request
APPROVE_WORDS = {"yes", "y", "approve", "approved", "confirm", "ok", "okay", "sure", "go ahead"}

app = FastAPI(title="Odoo AI Sales Agent")
agent = build_agent()


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    thread_id: str | None = Field(default=None, description="Omit to start a new conversation.")


class ChatResponse(BaseModel):
    thread_id: str
    reply: str
    awaiting_approval: bool = False
    pending_action: dict | None = None


def _pending_action(config: dict) -> dict | None:
    """The write action the agent is paused on, or None."""
    for interrupt in agent.get_state(config).interrupts:
        requests = interrupt.value.get("action_requests", [])
        if requests:
            return requests[0]
    return None


def _decision(text: str) -> dict:
    if text.strip().lower().rstrip(".!") in APPROVE_WORDS:
        return {"type": "approve"}
    return {"type": "reject", "message": f"User did not approve. User said: {text}"}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    thread_id = req.thread_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": MAX_STEPS}
    logger.info("thread=%s user: %s", thread_id, req.message)

    try:
        if _pending_action(config):
            decision = _decision(req.message)
            logger.info("thread=%s decision: %s", thread_id, decision["type"])
            agent.invoke(Command(resume={"decisions": [decision]}), config=config)
        else:
            agent.invoke({"messages": [{"role": "user", "content": req.message}]}, config=config)
    except GraphRecursionError:
        logger.error("thread=%s exceeded %s steps", thread_id, MAX_STEPS)
        raise HTTPException(status_code=500, detail="Agent exceeded its step limit. Try a simpler request.")
    except Exception:
        logger.exception("thread=%s agent failed", thread_id)
        raise HTTPException(status_code=500, detail="Agent failed. See server logs.")

    pending = _pending_action(config)
    last = agent.get_state(config).values["messages"][-1]
    reply = last.text or ""
    if pending:
        a = pending["args"]
        summary = f"Ready to create draft quotation: customer id {a.get('partner_id')}, product id {a.get('product_id')}, qty {a.get('qty')}."
        reply = f"{reply}\n\n{summary}" if reply else summary
        reply += "\nApproval needed. Reply 'yes' to create it, or tell me what to change."
    logger.info("thread=%s agent: %s", thread_id, reply)
    return ChatResponse(
        thread_id=thread_id,
        reply=reply.strip(),
        awaiting_approval=pending is not None,
        pending_action={"tool": pending["name"], "args": pending["args"]} if pending else None,
    )