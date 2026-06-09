"""
orchestrator.py
---------------
The central router. Call `run_pipeline(user_message)` to process any
customer message end-to-end through the multi-agent pipeline.
"""
import os
import anthropic
from dotenv import load_dotenv

from agents import (
    classify_message,
    handle_positive_feedback,
    handle_negative_feedback,
    handle_query,
)
from database import init_db, log_event

load_dotenv()


def get_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError("ANTHROPIC_API_KEY not set. Check your .env file.")
    return anthropic.Anthropic(api_key=api_key)


def run_pipeline(user_message: str, customer_name: str = "Customer") -> dict:
    """
    Full multi-agent pipeline:
      1. Classifier Agent  → determines message type
      2. Route to:
         - Feedback Handler (positive) → thank-you response
         - Feedback Handler (negative) → ticket creation + empathetic response
         - Query Handler               → ticket status lookup

    Returns a unified result dict with:
      - classification, reasoning, agent, response
      - ticket_created / ticket_queried (where applicable)
    """
    init_db()
    client = get_client()

    log_event("orchestrator", "pipeline_start", user_message[:100])

    classification_result = classify_message(client, user_message)
    cls = classification_result.get("classification", "query")

    if cls == "positive_feedback":
        result = handle_positive_feedback(client, user_message)
    elif cls == "negative_feedback":
        result = handle_negative_feedback(client, user_message, customer_name)
    else:
        result = handle_query(client, user_message)

    result["classification"] = cls
    result["reasoning"] = classification_result.get("reasoning", "")
    log_event("orchestrator", "pipeline_complete", f"cls={cls}")
    return result


if __name__ == "__main__":
    test_messages = [
        "Thanks for resolving my credit card issue so quickly!",
        "My debit card replacement still hasn't arrived after 3 weeks.",
        "Could you check the status of ticket 650932?",
    ]
    for msg in test_messages:
        print(f"\n{'='*60}")
        print(f"USER: {msg}")
        r = run_pipeline(msg)
        print(f"CLASSIFICATION : {r['classification']}")
        print(f"AGENT          : {r['agent']}")
        print(f"RESPONSE       : {r['response']}")
        if r.get("ticket_created"):
            print(f"TICKET CREATED : #{r['ticket_created']}")
        if r.get("ticket_queried"):
            print(f"TICKET QUERIED : #{r['ticket_queried']}")
