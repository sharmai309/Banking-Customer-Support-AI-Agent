import anthropic
from database import insert_ticket, generate_ticket_id, log_event

POSITIVE_SYSTEM_PROMPT = """You are a warm and professional banking customer support agent.
The customer has just left positive feedback. Write a brief, genuine, personalized thank-you response (2-3 sentences max).
Begin with: "Thank you for your kind words!"
Do NOT use placeholders like [CustomerName]. Keep it warm and conversational.
"""

NEGATIVE_SYSTEM_PROMPT = """You are an empathetic banking customer support agent.
The customer has reported a problem. A support ticket has already been created for them.
Write a brief, empathetic response (2-3 sentences) acknowledging their frustration and assuring them of follow-up.
You will be given the ticket number to include.
Begin with: "We apologize for the inconvenience."
"""


def handle_positive_feedback(client: anthropic.Anthropic, user_message: str) -> dict:
    """Generate a warm thank-you for positive feedback."""
    log_event("feedback_handler", "handling_positive", user_message[:80])

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=200,
        system=POSITIVE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    reply = response.content[0].text.strip()
    log_event("feedback_handler", "positive_response_generated", reply[:80])

    return {
        "agent": "feedback_handler",
        "type": "positive_feedback",
        "ticket_created": None,
        "response": reply,
    }


def handle_negative_feedback(client: anthropic.Anthropic, user_message: str, customer_name: str = "Customer") -> dict:
    """Create a ticket and generate an empathetic response for negative feedback."""
    log_event("feedback_handler", "handling_negative", user_message[:80])

    ticket_id = generate_ticket_id()
    ticket_issue = user_message[:100]
    insert_ticket(ticket_id, customer_name, ticket_issue)
    log_event("feedback_handler", "ticket_created", f"#{ticket_id} for '{ticket_issue[:60]}'")

    prompt = (
        f"Customer complaint: {user_message}\n\n"
        f"Ticket #{ticket_id} has been created. Include this ticket number in your response."
    )

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=250,
        system=NEGATIVE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    reply = response.content[0].text.strip()
    log_event("feedback_handler", "negative_response_generated", reply[:80])

    return {
        "agent": "feedback_handler",
        "type": "negative_feedback",
        "ticket_created": ticket_id,
        "response": reply,
    }
