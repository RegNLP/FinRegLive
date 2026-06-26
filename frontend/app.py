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

    try:
        diagnostics = api_get("/diagnostics")
    except requests.RequestException:
        return

    database = diagnostics["database"]
    sources = diagnostics.get("sources", [])

    st.sidebar.subheader("Dataset")
    metric_a, metric_b = st.sidebar.columns(2)
    metric_a.metric("Documents", database["document_count"])
    metric_b.metric("Chunks", database["chunk_count"])

    with st.sidebar.expander("Sources", expanded=False):
        for source in sources:
            st.write(f"{source['source_name']} ({source['source_type']})")


def render_sources(sources: list[dict[str, Any]]) -> None:
    if not sources:
        st.info("No sources returned.")
        return

    for index, source in enumerate(sources, start=1):
        with st.expander(f"{index}. {source['title']}", expanded=index == 1):
            st.write(source["source_name"])
            st.link_button("Open source", source["source_url"])
            st.code(f"chunk_id: {source['chunk_id']}", language="text")


def render_retrieval_results(title: str, results: list[dict[str, Any]]) -> None:
    st.markdown(f"**{title}**")
    if not results:
        st.info("No results.")
        return

    for result in results:
        label = f"{result['rank']}. {result['source_name']} | {result['title']}"
        with st.expander(label):
            st.metric("Score", round(result["score"], 6))
            st.caption(result["source_url"])
            st.code(f"chunk_id: {result['chunk_id']}", language="text")
            st.write(result["chunk_text"])


def render_document_summary(document: dict[str, Any]) -> None:
    title = document["title"]
    source_name = document["source_name"]
    publication_date = document["publication_date"] or "No publication date"
    chunk_count = document["chunk_count"]
    text_length = document["text_length"]

    with st.expander(title):
        meta_a, meta_b, meta_c, meta_d = st.columns(4)
        meta_a.metric("Document ID", document["id"])
        meta_b.metric("Source", source_name)
        meta_c.metric("Chunks", chunk_count)
        meta_d.metric("Text chars", text_length)
        st.caption(publication_date)
        st.link_button("Open source", document["source_url"])


def render_recent_updates_page() -> None:
    st.header("Recent Updates")

    with st.expander("Fetch New Data", expanded=False):
        source_options = {
            "All active sources": "all",
            "SEC press releases": "sec_press",
            "SEC EDGAR filings": "sec_edgar",
            "FCA news": "fca_news",
            "FCA publications": "fca_publications",
            "Bank of England news": "boe_news",
            "Bank of England publications": "boe_publications",
            "Bank of England PRA": "boe_prudential",
        }
        selected_source_label = st.selectbox("Source", options=list(source_options))
        fetch_col_a, fetch_col_b = st.columns(2)
        with fetch_col_a:
            fetch_days = st.number_input("Days", min_value=1, max_value=90, value=7)
        with fetch_col_b:
            fetch_limit = st.number_input("Limit per source", min_value=1, max_value=100, value=20)

        if st.button("Fetch newest documents"):
            try:
                result = api_post(
                    "/ingest/recent",
                    {
                        "days": fetch_days,
                        "source": source_options[selected_source_label],
                        "limit": fetch_limit,
                        "recreate_index": True,
                    },
                )
            except requests.RequestException as exc:
                st.error(f"Ingestion failed: {exc}")
                return

            st.success(
                "Fetched "
                f"{result['fetched_documents']} documents, stored {result['stored']}, "
                f"duplicates {result['duplicates']}, indexed {result['chunks_indexed']} chunks."
            )
            if result["source_failures"]:
                st.warning("Some sources failed.")
                for failure in result["source_failures"]:
                    st.write(f"- {failure}")

    limit = st.slider("Updates to show", min_value=1, max_value=50, value=10)

    try:
        documents = api_get(f"/recent-updates?limit={limit}")
    except requests.RequestException as exc:
        st.error(f"Recent updates failed: {exc}")
        return

    if not documents:
        st.info("No documents found. Run ingestion first.")
        return

    for document in documents:
        render_document_summary(document)

    st.subheader("Inspect Document")
    document_options = {
        f"{document['id']} | {document['title']}": document["id"] for document in documents
    }
    selected_label = st.selectbox("Document", options=list(document_options))

    if st.button("Load document"):
        document_id = document_options[selected_label]
        try:
            st.session_state["selected_document"] = api_get(f"/documents/{document_id}")
        except requests.RequestException as exc:
            st.error(f"Document load failed: {exc}")
            return

    selected_document = st.session_state.get("selected_document")
    if not selected_document:
        return

    st.write(selected_document["title"])
    st.caption(selected_document["source_url"])

    with st.expander("Document text", expanded=False):
        st.write(selected_document["text"] or "No document text stored.")

    with st.expander("Chunks", expanded=True):
        if not selected_document["chunks"]:
            st.info("No chunks stored for this document.")
        for chunk in selected_document["chunks"]:
            st.markdown(f"**Chunk {chunk['chunk_index']}**")
            st.write(chunk["text"])


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
        col_a, col_b, col_c = st.columns([1, 1, 1])
        with col_a:
            top_k = st.slider("Sources", min_value=1, max_value=10, value=2)
        with col_b:
            use_llm = st.toggle("OpenAI answer", value=False)
        with col_c:
            use_reranking = st.toggle("Rerank evidence", value=False)

        submitted = st.form_submit_button("Run query")

    if submitted:
        try:
            st.session_state["last_answer"] = api_post(
                "/query",
                {
                    "question": question,
                    "top_k": top_k,
                    "use_llm": use_llm,
                    "use_reranking": use_reranking,
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

    st.subheader("Configured Sources")
    st.dataframe(
        diagnostics.get("sources", []),
        hide_index=True,
        use_container_width=True,
    )

    st.json(diagnostics)


def render_analytics_page() -> None:
    st.header("Analytics")

    try:
        analytics = api_get("/analytics/corpus")
    except requests.RequestException as exc:
        st.error(f"Analytics failed: {exc}")
        return

    total_a, total_b = st.columns(2)
    total_a.metric("Documents", analytics["total_documents"])
    total_b.metric("Chunks", analytics["total_chunks"])

    st.subheader("Length Stats")
    document_stats = analytics["document_length_stats"]
    chunk_stats = analytics["chunk_length_stats"]

    doc_a, doc_b, doc_c = st.columns(3)
    doc_a.metric("Document min words", document_stats["min_words"])
    doc_b.metric("Document avg words", document_stats["avg_words"])
    doc_c.metric("Document max words", document_stats["max_words"])

    chunk_a, chunk_b, chunk_c = st.columns(3)
    chunk_a.metric("Chunk min words", chunk_stats["min_words"])
    chunk_b.metric("Chunk avg words", chunk_stats["avg_words"])
    chunk_c.metric("Chunk max words", chunk_stats["max_words"])

    st.subheader("Source Coverage")
    st.dataframe(
        analytics["sources"],
        hide_index=True,
        use_container_width=True,
    )

    st.subheader("Recent Ingestion Runs")
    st.dataframe(
        analytics["recent_ingestion_runs"],
        hide_index=True,
        use_container_width=True,
    )


def render_retrieval_diagnostics_page() -> None:
    st.header("Retrieval Diagnostics")

    with st.form("retrieval_diagnostics_form"):
        question = st.text_area(
            "Question",
            value="What recent FCA updates mention listing rules or investment funds?",
            height=100,
        )
        top_k = st.slider("Results per method", min_value=1, max_value=20, value=5)
        submitted = st.form_submit_button("Compare retrieval")

    if submitted:
        try:
            st.session_state["retrieval_diagnostics"] = api_post(
                "/retrieval/diagnostics",
                {
                    "question": question,
                    "top_k": top_k,
                },
            )
        except requests.RequestException as exc:
            st.error(f"Retrieval diagnostics failed: {exc}")
            return

    diagnostics = st.session_state.get("retrieval_diagnostics")
    if not diagnostics:
        return

    overlap = diagnostics["overlap"]
    overlap_a, overlap_b, overlap_c, overlap_d = st.columns(4)
    overlap_a.metric("BM25 & Vector", overlap["bm25_vector"])
    overlap_b.metric("BM25 & Hybrid", overlap["bm25_hybrid"])
    overlap_c.metric("Vector & Hybrid", overlap["vector_hybrid"])
    overlap_d.metric("All methods", overlap["all_methods"])

    bm25_col, vector_col, hybrid_col = st.columns(3)
    with bm25_col:
        render_retrieval_results("BM25", diagnostics["bm25"])
    with vector_col:
        render_retrieval_results("Vector", diagnostics["vector"])
    with hybrid_col:
        render_retrieval_results("Hybrid", diagnostics["hybrid"])


def main() -> None:
    st.set_page_config(
        page_title="FinReg Live Intelligence",
        page_icon=None,
        layout="wide",
    )

    st.title("FinReg Live Intelligence")
    show_api_status()

    ask_tab, recent_updates_tab, retrieval_tab, analytics_tab, diagnostics_tab = st.tabs(
        ["Ask", "Recent Updates", "Retrieval", "Analytics", "Diagnostics"]
    )
    with ask_tab:
        render_ask_page()
    with recent_updates_tab:
        render_recent_updates_page()
    with retrieval_tab:
        render_retrieval_diagnostics_page()
    with analytics_tab:
        render_analytics_page()
    with diagnostics_tab:
        render_diagnostics_page()


if __name__ == "__main__":
    main()
