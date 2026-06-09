import re
import anthropic
from database import get_ticket, log_event

EXTRACTOR_SYSTEM_PROMPT = """Extract the support ticket number from the user's message.
A ticket number is a 6-digit numeric code.
Respond with ONLY a JSON object — no markdown, no extra text:
{"ticket_id": "<6-digit number or null if not found>"}
"""

QUERY_RESPONSE_SYSTEM_PROMPT = """You are a helpful banking customer support agent providing a ticket status update.
Write a clear, professional one-sentence response.
Use the format: "Your ticket #[ID] is currently marked as: [Status]."
If the ticket was not found, politely say so and suggest the customer double-check their ticket number.
"""


def _extract_ticket_id(client: anthropic.Anthropic, user_message: str) -> str | None:
    regex_match = re.search(r'\b(\d{6})\b', user_message)
    if regex_match:
        return regex_match.group(1)

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=100,
        system=EXTRACTOR_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )
    import json
    try:
        data = json.loads(response.content[0].text.strip())
        return data.get("ticket_id")
    except Exception:
        return None


def handle_query(client: anthropic.Anthropic, user_message: str) -> dict:
    """Extract ticket number, look it up in the DB, and return a status response."""
    log_event("query_handler", "handling_query", user_message[:80])

    ticket_id = _extract_ticket_id(client, user_message)
    log_event("query_handler", "ticket_extracted", f"#{ticket_id}")

    ticket = get_ticket(ticket_id) if ticket_id else None

    if ticket:
        status = ticket["status"].replace("_", " ")
        context = f"Ticket #{ticket_id} status: {status}. Issue: {ticket['issue']}."
        log_event("query_handler", "ticket_found", f"#{ticket_id} → {status}")
    else:
        context = f"Ticket #{ticket_id} was not found in the database." if ticket_id else "No ticket number found in the user's message."
        log_event("query_handler", "ticket_not_found", f"#{ticket_id}")

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=150,
        system=QUERY_RESPONSE_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"User message: {user_message}\n\nDatabase result: {context}"}],
    )

    reply = response.content[0].text.strip()
    log_event("query_handler", "query_response_generated", reply[:80])

    return {
        "agent": "query_handler",
        "type": "query",
        "ticket_queried": ticket_id,
        "ticket_found": ticket is not None,
        "ticket_data": ticket,
        "response": reply,
    }
