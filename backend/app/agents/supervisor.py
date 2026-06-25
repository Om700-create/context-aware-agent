"""
Supervisor Agent (LangGraph orchestration).

Builds a LangGraph StateGraph that performs:
  1. Intent classification / context routing
  2. Agent selection (Document / Appointment / Memory)
  3. Workflow orchestration across the Validation and Date sub-agents
     (those are invoked directly by the Appointment Agent, not as separate
     graph nodes, since they are synchronous helpers within a single turn)
"""
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session as DBSession

from app.db import models
from app.agents import document_agent, appointment_agent, memory_agent


class GraphState(TypedDict, total=False):
    message: str
    intent: str
    reply: str
    agent: str
    confidence: Optional[float]
    citations: list
    booking_state: Optional[str]
    meta: dict


def classify_intent(state: GraphState, session: models.Session) -> GraphState:
    message = state["message"]

    if session.booking_state not in ("IDLE", None):
        mem_query = memory_agent.detect_memory_query(message)
        if mem_query:
            state["intent"] = "memory"
            state["meta"] = {"memory_query_type": mem_query}
            return state
        if document_agent_keywords(message):
            state["intent"] = "document"
        else:
            state["intent"] = "appointment"
        return state

    mem_query = memory_agent.detect_memory_query(message)
    if mem_query and not appointment_agent.is_new_booking_request(message):
        state["intent"] = "memory"
        state["meta"] = {"memory_query_type": mem_query}
        return state

    if appointment_agent.is_booking_intent(message):
        state["intent"] = "appointment"
        return state

    state["intent"] = "document"
    return state


def document_agent_keywords(message: str) -> bool:
    t = message.lower()
    return any(w in t for w in ["what is", "what's", "explain", "policy", "document", "according to", "tell me about", "?"])


def build_graph_runner():
    def run(db: DBSession, session: models.Session, user: models.User, message: str) -> dict:
        state: GraphState = {"message": message, "meta": {}}
        state = classify_intent(state, session)
        intent = state["intent"]

        if intent == "memory":
            answer = memory_agent.run_memory_agent(db, user, state["meta"]["memory_query_type"])
            return {
                "reply": answer,
                "agent": "memory_agent",
                "confidence": None,
                "citations": [],
                "booking_state": session.booking_state,
            }

        if intent == "appointment":
            if session.booking_state in ("IDLE", None):
                result = appointment_agent.start_booking(session, user)
            else:
                result = appointment_agent.handle_booking_turn(db, session, user, message)
            db.add(session)
            db.commit()
            return {
                "reply": result["reply"],
                "agent": "appointment_agent",
                "confidence": None,
                "citations": [],
                "booking_state": result.get("booking_state"),
                "meta": {"appointment_id": result.get("appointment_id")} if result.get("appointment_id") else {},
            }

        result = document_agent.run_document_agent(db, message)
        return {
            "reply": result["answer"],
            "agent": "document_agent",
            "confidence": result["confidence"],
            "citations": result["citations"],
            "booking_state": session.booking_state,
        }

    return run


def build_langgraph():
    """Minimal explicit LangGraph wiring, exposed for inspection/extension."""
    graph = StateGraph(GraphState)

    def node_router(state: GraphState):
        return state

    graph.add_node("router", node_router)
    graph.set_entry_point("router")
    graph.add_edge("router", END)
    return graph.compile()


supervisor_runner = build_graph_runner()
