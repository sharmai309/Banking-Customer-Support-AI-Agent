"""
evaluation.py
-------------
Part 2: LLMOps — Model Evaluation
Runs a test suite against the multi-agent pipeline and scores each response.
"""
import json
import anthropic
import os
from dotenv import load_dotenv
from orchestrator import run_pipeline, get_client

load_dotenv()

TEST_CASES = [
    {
        "id": "TC01",
        "input": "Thanks for resolving my credit card issue so quickly!",
        "expected_classification": "positive_feedback",
        "expected_keywords": ["thank you", "kind words", "happy", "delight"],
    },
    {
        "id": "TC02",
        "input": "Your service is amazing, you helped me fix my net banking.",
        "expected_classification": "positive_feedback",
        "expected_keywords": ["thank", "glad", "pleased", "support"],
    },
    {
        "id": "TC03",
        "input": "My debit card replacement still hasn't arrived after 3 weeks.",
        "expected_classification": "negative_feedback",
        "expected_keywords": ["apologize", "ticket", "follow up", "team"],
    },
    {
        "id": "TC04",
        "input": "I'm very unhappy. My loan EMI was deducted twice this month.",
        "expected_classification": "negative_feedback",
        "expected_keywords": ["apologize", "inconvenience", "ticket"],
    },
    {
        "id": "TC05",
        "input": "Could you check the status of ticket 650932?",
        "expected_classification": "query",
        "expected_keywords": ["650932", "resolved", "marked"],
    },
    {
        "id": "TC06",
        "input": "What is the current status of my ticket 999001?",
        "expected_classification": "query",
        "expected_keywords": ["999001", "progress", "status"],
    },
]

EVALUATOR_SYSTEM = """You are an LLM response quality evaluator for a banking customer support system.
Score the response on these dimensions (each 0–10):
- empathy: How empathetic and human does the response feel?
- clarity: How clear and easy to understand is the response?
- relevance: How relevant is the response to the customer's message?
- professionalism: How professional and appropriate is the tone?

Respond with ONLY valid JSON:
{"empathy": N, "clarity": N, "relevance": N, "professionalism": N, "overall_comment": "..."}
"""


def evaluate_response(client: anthropic.Anthropic, user_message: str, agent_response: str) -> dict:
    prompt = f"Customer message: {user_message}\n\nAgent response: {agent_response}"
    resp = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=300,
        system=EVALUATOR_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    try:
        return json.loads(resp.content[0].text.strip())
    except Exception:
        return {"empathy": 0, "clarity": 0, "relevance": 0, "professionalism": 0, "overall_comment": "parse error"}


def run_evaluation() -> list[dict]:
    client = get_client()
    results = []

    print("\n" + "=" * 70)
    print("  BANKING SUPPORT AI — MODEL EVALUATION REPORT")
    print("=" * 70)

    for tc in TEST_CASES:
        print(f"\n[{tc['id']}] Input: {tc['input'][:60]}...")

        pipeline_result = run_pipeline(tc["input"])
        cls = pipeline_result["classification"]
        response_text = pipeline_result["response"]

        cls_correct = cls == tc["expected_classification"]

        kw_hits = sum(1 for kw in tc["expected_keywords"] if kw.lower() in response_text.lower())
        kw_score = round((kw_hits / len(tc["expected_keywords"])) * 10, 1)

        scores = evaluate_response(client, tc["input"], response_text)

        overall = round(
            (scores.get("empathy", 0) + scores.get("clarity", 0) +
             scores.get("relevance", 0) + scores.get("professionalism", 0)) / 4, 1
        )

        result = {
            "test_id": tc["id"],
            "input": tc["input"],
            "expected_classification": tc["expected_classification"],
            "actual_classification": cls,
            "classification_correct": cls_correct,
            "response": response_text,
            "keyword_score": kw_score,
            "empathy_score": scores.get("empathy", 0),
            "clarity_score": scores.get("clarity", 0),
            "relevance_score": scores.get("relevance", 0),
            "professionalism_score": scores.get("professionalism", 0),
            "overall_score": overall,
            "comment": scores.get("overall_comment", ""),
        }
        results.append(result)

        cls_icon = "✅" if cls_correct else "❌"
        print(f"  Classification : {cls_icon} {cls} (expected: {tc['expected_classification']})")
        print(f"  Keyword score  : {kw_score}/10")
        print(f"  Quality scores : Empathy={scores.get('empathy')}, Clarity={scores.get('clarity')}, "
              f"Relevance={scores.get('relevance')}, Professionalism={scores.get('professionalism')}")
        print(f"  Overall        : {overall}/10")
        print(f"  Comment        : {scores.get('overall_comment', '')}")

    total = len(results)
    correct = sum(1 for r in results if r["classification_correct"])
    avg_overall = round(sum(r["overall_score"] for r in results) / total, 1)

    print("\n" + "=" * 70)
    print(f"  SUMMARY")
    print(f"  Classification accuracy : {correct}/{total} ({round(correct/total*100)}%)")
    print(f"  Average quality score   : {avg_overall}/10")
    print("=" * 70 + "\n")

    return results


if __name__ == "__main__":
    run_evaluation()
