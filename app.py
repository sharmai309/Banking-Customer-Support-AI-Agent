"""
app.py  —  Banking Customer Support AI Agent  (Streamlit UI)
Run with:  streamlit run app.py
"""
import streamlit as st
import pandas as pd
from datetime import datetime

from database import init_db, get_all_tickets, get_logs
from orchestrator import run_pipeline

init_db()

st.set_page_config(
    page_title="Banking Support AI Agent",
    page_icon="🏦",
    layout="wide",
)

st.markdown("""
<style>
.agent-tag {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 500;
    margin-bottom: 6px;
}
.tag-positive  { background: #d1fae5; color: #065f46; }
.tag-negative  { background: #fee2e2; color: #991b1b; }
.tag-query     { background: #dbeafe; color: #1e40af; }
.tag-classifier{ background: #fef3c7; color: #92400e; }
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "stats" not in st.session_state:
    st.session_state.stats = {"total": 0, "positive": 0, "negative": 0, "queries": 0}

st.title("🏦 Banking Customer Support AI Agent")
st.caption("Multi-agent system · Classifier → Feedback Handler / Query Handler")

tab_chat, tab_tickets, tab_logs, tab_eval = st.tabs(
    ["💬 Chat", "🎫 Ticket Database", "📋 Agent Logs", "📊 Evaluation"]
)

with tab_chat:
    col_chat, col_sidebar = st.columns([2, 1])

    with col_chat:
        st.subheader("Customer chat")

        chat_container = st.container(height=420)
        with chat_container:
            if not st.session_state.messages:
                st.info("No messages yet. Type something below to begin.")
            for m in st.session_state.messages:
                if m["role"] == "user":
                    with st.chat_message("user"):
                        st.write(m["content"])
                else:
                    with st.chat_message("assistant"):
                        cls = m.get("classification", "query")
                        tag_map = {
                            "positive_feedback": ("positive", "Feedback handler · positive"),
                            "negative_feedback": ("negative", "Feedback handler · negative"),
                            "query":             ("query",    "Query handler"),
                        }
                        tag_cls, tag_label = tag_map.get(cls, ("query", "Query handler"))
                        st.markdown(
                            f'<span class="agent-tag tag-classifier">Classifier: {cls.replace("_"," ")}</span> '
                            f'<span class="agent-tag tag-{tag_cls}">{tag_label}</span>',
                            unsafe_allow_html=True,
                        )
                        st.write(m["content"])
                        if m.get("ticket_created"):
                            st.success(f"🎫 Ticket #{m['ticket_created']} created in database")
                        if m.get("ticket_queried"):
                            found = m.get("ticket_found", False)
                            if found:
                                st.info(f"🔍 Looked up ticket #{m['ticket_queried']}")
                            else:
                                st.warning(f"🔍 Ticket #{m['ticket_queried']} not found")

        st.divider()

        with st.expander("💡 Quick test messages"):
            cols = st.columns(3)
            examples = {
                "Positive": "Thanks for resolving my credit card issue so quickly!",
                "Negative": "My debit card replacement still hasn't arrived after 3 weeks.",
                "Query #650932": "Could you check the status of ticket 650932?",
                "Query #999001": "What is the status of my ticket 999001?",
                "Positive #2": "Your team was incredibly helpful with my net banking issue.",
                "Negative #2": "I'm very unhappy. My loan EMI was deducted twice.",
            }
            for i, (label, msg) in enumerate(examples.items()):
                if cols[i % 3].button(label, use_container_width=True):
                    st.session_state["prefill"] = msg

        user_input = st.chat_input("Type your message…")
        if "prefill" in st.session_state:
            user_input = st.session_state.pop("prefill")

        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})

            with st.spinner("Agents processing…"):
                try:
                    result = run_pipeline(user_input)
                    cls = result["classification"]
                    st.session_state.stats["total"] += 1
                    if cls == "positive_feedback":
                        st.session_state.stats["positive"] += 1
                    elif cls == "negative_feedback":
                        st.session_state.stats["negative"] += 1
                    else:
                        st.session_state.stats["queries"] += 1

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result["response"],
                        "classification": cls,
                        "ticket_created": result.get("ticket_created"),
                        "ticket_queried": result.get("ticket_queried"),
                        "ticket_found": result.get("ticket_found"),
                    })
                except Exception as e:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"⚠️ Error: {e}",
                        "classification": "query",
                    })
            st.rerun()

    with col_sidebar:
        st.subheader("Session stats")
        s = st.session_state.stats
        c1, c2 = st.columns(2)
        c1.metric("Messages", s["total"])
        c2.metric("Tickets created", s["negative"])
        c1.metric("Positive", s["positive"])
        c2.metric("Queries", s["queries"])

        st.subheader("Recent tickets")
        tickets = get_all_tickets()
        if tickets:
            for t in tickets[:5]:
                status_color = {"resolved": "🟢", "unresolved": "🔴", "in_progress": "🟡"}.get(t["status"], "⚪")
                st.markdown(f"**#{t['ticket_id']}** {status_color} `{t['status']}`")
                st.caption(t["issue"][:50] + ("…" if len(t["issue"]) > 50 else ""))
        else:
            st.caption("No tickets yet.")

with tab_tickets:
    st.subheader("Support tickets database")
    tickets = get_all_tickets()
    if tickets:
        df = pd.DataFrame(tickets)
        df["status"] = df["status"].str.replace("_", " ")

        status_filter = st.multiselect(
            "Filter by status",
            options=["resolved", "unresolved", "in progress"],
            default=["resolved", "unresolved", "in progress"],
        )
        mask = df["status"].isin(status_filter)
        st.dataframe(
            df[mask][["ticket_id", "customer", "issue", "status", "created_at", "updated_at"]],
            use_container_width=True,
            hide_index=True,
        )
        c1, c2, c3 = st.columns(3)
        c1.metric("Total tickets", len(df))
        c2.metric("Resolved", len(df[df["status"] == "resolved"]))
        c3.metric("Unresolved", len(df[df["status"] == "unresolved"]))
    else:
        st.info("No tickets in the database yet.")

with tab_logs:
    st.subheader("Agent event log")
    logs = get_logs(100)
    if logs:
        agent_filter = st.multiselect(
            "Filter by agent",
            options=["orchestrator", "classifier", "feedback_handler", "query_handler"],
            default=["orchestrator", "classifier", "feedback_handler", "query_handler"],
        )
        filtered = [l for l in logs if l["agent"] in agent_filter]
        df_logs = pd.DataFrame(filtered)
        color_map = {
            "orchestrator":    "🔵",
            "classifier":      "🟡",
            "feedback_handler":"🟢",
            "query_handler":   "🔷",
        }
        df_logs["agent"] = df_logs["agent"].apply(lambda a: f"{color_map.get(a,'⚪')} {a}")
        st.dataframe(
            df_logs[["timestamp", "agent", "event", "details"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No logs yet. Send a message in the Chat tab.")

with tab_eval:
    st.subheader("Model evaluation — Part 2 LLMOps")
    st.info(
        "Running the full evaluation calls the Anthropic API for each test case (6 cases × 2 calls each). "
        "This will take ~30–60 seconds and will appear in the terminal / logs."
    )

    if st.button("▶ Run evaluation suite", type="primary"):
        from evaluation import run_evaluation, TEST_CASES

        with st.spinner("Running evaluation…"):
            results = run_evaluation()

        st.success("Evaluation complete!")

        df_eval = pd.DataFrame(results)
        total = len(df_eval)
        correct = df_eval["classification_correct"].sum()
        avg_overall = df_eval["overall_score"].mean()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Classification accuracy", f"{correct}/{total}")
        c2.metric("Avg quality score", f"{avg_overall:.1f}/10")
        c3.metric("Avg empathy", f"{df_eval['empathy_score'].mean():.1f}/10")
        c4.metric("Avg clarity", f"{df_eval['clarity_score'].mean():.1f}/10")

        st.subheader("Per-test results")
        display_cols = [
            "test_id", "expected_classification", "actual_classification",
            "classification_correct", "keyword_score",
            "empathy_score", "clarity_score", "relevance_score",
            "professionalism_score", "overall_score",
        ]
        st.dataframe(df_eval[display_cols], use_container_width=True, hide_index=True)

        st.subheader("Responses")
        for _, row in df_eval.iterrows():
            with st.expander(f"[{row['test_id']}] {row['input'][:60]}…"):
                st.markdown(f"**Classification:** {row['actual_classification']} {'✅' if row['classification_correct'] else '❌'}")
                st.markdown(f"**Response:** {row['response']}")
                st.markdown(f"**Evaluator comment:** _{row['comment']}_")
    else:
        st.markdown("### Test cases")
        from evaluation import TEST_CASES
        for tc in TEST_CASES:
            st.markdown(f"**{tc['id']}** — `{tc['expected_classification']}` → _{tc['input']}_")
