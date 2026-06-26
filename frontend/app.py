# Step 10 - Streamlit Frontend
#
# Role:
#   Provide a browser UI for querying the RAG backend, reviewing sources,
#   submitting feedback, and checking diagnostics.
#
# Why this exists:
#   Terminal commands prove the pipeline works, but users need a simple
#   interface for asking questions and reviewing evidence.
#
# Input:
#   User questions, retrieval settings, answer mode, and feedback labels.
#
# Output:
#   Streamlit pages that call the FastAPI backend and display structured
#   responses.

import os
from typing import Any

import requests
import streamlit as st


DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT_SECONDS = 120


def get_api_base_url() -> str:
    return os.getenv("FINREG_API_BASE_URL", DEFAULT_API_BASE_URL).rstrip("/")


def api_get(path: str) -> dict[str, Any]:
    response = requests.get(
        f"{get_api_base_url()}{path}",
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def api_post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(
        f"{get_api_base_url()}{path}",
        json=payload,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    return response.json()


def show_api_status() -> None:
    st.sidebar.caption(get_api_base_url())

    try:
        health = api_get("/health")
    except requests.RequestException:
        st.sidebar.error("Backend unavailable")
        return

    if health.get("status") == "ok":
        st.sidebar.success("Backend online")
    else:
        st.sidebar.warning("Backend status unknown")


def render_sources(sources: list[dict[str, Any]]) -> None:
    if not sources:
        st.info("No sources returned.")
        return

    for index, source in enumerate(sources, start=1):
        with st.expander(f"{index}. {source['title']}", expanded=index == 1):
            st.write(source["source_name"])
            st.link_button("Open source", source["source_url"])
            st.code(f"chunk_id: {source['chunk_id']}", language="text")


def render_feedback_form(query_id: int) -> None:
    with st.form("feedback_form"):
        useful_label = st.selectbox(
            "Usefulness",
            options=["useful", "not_useful", "unsure"],
        )
        correctness_label = st.selectbox(
            "Correctness",
            options=["correct", "incorrect", "unsure"],
        )
        evidence_label = st.selectbox(
            "Evidence",
            options=["supported", "weak", "missing", "unsure"],
        )
        note = st.text_area("Note", height=90)

        submitted = st.form_submit_button("Submit feedback")

    if not submitted:
        return

    try:
        feedback = api_post(
            "/feedback",
            {
                "query_id": query_id,
                "useful_label": useful_label,
                "correctness_label": correctness_label,
                "evidence_label": evidence_label,
                "note": note or None,
            },
        )
    except requests.RequestException as exc:
        st.error(f"Feedback failed: {exc}")
        return

    st.success(f"Feedback stored: {feedback['feedback_id']}")


def render_ask_page() -> None:
    st.header("Ask")

    with st.form("query_form"):
        question = st.text_area(
            "Question",
            value="What did the SEC and CFTC publish about derivatives?",
            height=120,
        )
        col_a, col_b = st.columns([1, 1])
        with col_a:
            top_k = st.slider("Sources", min_value=1, max_value=10, value=2)
        with col_b:
            use_llm = st.toggle("OpenAI answer", value=False)

        submitted = st.form_submit_button("Run query")

    if submitted:
        try:
            st.session_state["last_answer"] = api_post(
                "/query",
                {
                    "question": question,
                    "top_k": top_k,
                    "use_llm": use_llm,
                },
            )
        except requests.RequestException as exc:
            st.error(f"Query failed: {exc}")
            return

    answer = st.session_state.get("last_answer")
    if not answer:
        return

    st.subheader("Answer")
    st.write(answer["answer"])

    meta_a, meta_b = st.columns([1, 1])
    meta_a.metric("Query ID", answer["query_id"])
    meta_b.metric("Sources", len(answer["sources"]))

    st.subheader("Sources")
    render_sources(answer["sources"])

    st.subheader("Limitations")
    for limitation in answer["limitations"]:
        st.write(f"- {limitation}")

    st.subheader("Feedback")
    render_feedback_form(answer["query_id"])


def render_diagnostics_page() -> None:
    st.header("Diagnostics")

    try:
        diagnostics = api_get("/diagnostics")
    except requests.RequestException as exc:
        st.error(f"Diagnostics failed: {exc}")
        return

    database = diagnostics["database"]
    search = diagnostics["search"]

    st.subheader("Database")
    db_a, db_b, db_c, db_d = st.columns(4)
    db_a.metric("Documents", database["document_count"])
    db_b.metric("Chunks", database["chunk_count"])
    db_c.metric("Queries", database["query_count"])
    db_d.metric("Feedback", database["feedback_count"])

    st.subheader("Search")
    search_a, search_b, search_c = st.columns(3)
    search_a.metric("Status", search["status"])
    search_b.metric("Index", "exists" if search["index_exists"] else "missing")
    search_c.metric("Indexed chunks", search["indexed_chunk_count"] or 0)

    st.json(diagnostics)


def main() -> None:
    st.set_page_config(
        page_title="FinReg Live Intelligence",
        page_icon=None,
        layout="wide",
    )

    st.title("FinReg Live Intelligence")
    show_api_status()

    ask_tab, diagnostics_tab = st.tabs(["Ask", "Diagnostics"])
    with ask_tab:
        render_ask_page()
    with diagnostics_tab:
        render_diagnostics_page()


if __name__ == "__main__":
    main()
