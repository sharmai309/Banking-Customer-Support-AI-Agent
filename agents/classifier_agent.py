import json
import anthropic
from database import log_event

CLASSIFIER_SYSTEM_PROMPT = """You are a banking customer support classifier.

Your ONLY job is to classify an incoming user message into exactly one of these three categories:
- positive_feedback  : The customer is expressing satisfaction or gratitude
- negative_feedback  : The customer is complaining or reporting an unresolved problem
- query              : The customer is asking about the status of an existing ticket

Respond with ONLY a valid JSON object — no markdown, no extra text:
{
  "classification": "<positive_feedback | negative_feedback | query>",
  "reasoning": "<one short sentence explaining why>"
}
"""


def classify_message(client: anthropic.Anthropic, user_message: str) -> dict:
    """
    Classifies a user message and returns:
      {
        "classification": "positive_feedback" | "negative_feedback" | "query",
        "reasoning": "..."
      }
    """
    log_event("classifier", "received_message", user_message[:100])

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=200,
        system=CLASSIFIER_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    raw = response.content[0].text.strip()

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        result = {"classification": "query", "reasoning": "Could not parse; defaulting to query."}

    log_event("classifier", "classified", f"{result.get('classification')} — {result.get('reasoning', '')}")
    return result
