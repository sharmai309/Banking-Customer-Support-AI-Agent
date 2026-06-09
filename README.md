# Banking Customer Support AI Agent

Multi-agent GenAI system built for the Applied Generative AI Specialisation capstone.

## Architecture

```
User Message
     │
     ▼
┌─────────────────┐
│ Classifier Agent │  ──► positive_feedback ──► Feedback Handler (thank-you)
│  (claude API)   │  ──► negative_feedback ──► Feedback Handler (ticket + empathy)
└─────────────────┘  ──► query             ──► Query Handler (ticket lookup)
```

### Agents
| Agent | File | Responsibility |
|---|---|---|
| Classifier | `agents/classifier_agent.py` | Routes message to correct handler |
| Feedback Handler | `agents/feedback_agent.py` | Positive thank-you / Negative ticket creation |
| Query Handler | `agents/query_agent.py` | Ticket status lookup |
| Orchestrator | `orchestrator.py` | Ties all agents together |

### Database
SQLite (`support_tickets.db`) with two tables:
- `support_tickets` — ticket records
- `agent_logs` — event log from all agents

---

## Setup

### 1. Clone / open the project in VS Code

```bash
code banking_support_agent
```

### 2. Create a virtual environment

```bash
python -m venv venv

# macOS / Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Add your API key

```bash
cp .env.example .env
# Open .env and replace "your_api_key_here" with your actual Anthropic API key
```

---

## Run

### Streamlit UI (recommended)

```bash
streamlit run app.py
```

Opens at **http://localhost:8501**

### CLI test (quick check)

```bash
python orchestrator.py
```

### Evaluation only

```bash
python -m evaluation.evaluate
```

---

## Project structure

```
banking_support_agent/
├── app.py                  ← Streamlit dashboard (Part 2 UI)
├── orchestrator.py         ← Main pipeline router
├── requirements.txt
├── .env.example
├── agents/
│   ├── __init__.py
│   ├── classifier_agent.py ← Classifier Agent
│   ├── feedback_agent.py   ← Feedback Handler Agent
│   └── query_agent.py      ← Query Handler Agent
├── database/
│   ├── __init__.py
│   └── db.py               ← SQLite helpers
└── evaluation/
    ├── __init__.py
    └── evaluate.py         ← LLMOps evaluation (Part 2)
```

---

## Sample outputs

| Input | Classification | Response |
|---|---|---|
| "Thanks for resolving my credit card issue!" | positive_feedback | "Thank you for your kind words! We're delighted to assist you." |
| "My debit card still hasn't arrived." | negative_feedback | "We apologize… ticket #XXXXXX has been created." |
| "Check status of ticket 650932" | query | "Your ticket #650932 is currently marked as: resolved." |
