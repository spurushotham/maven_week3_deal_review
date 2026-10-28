import logging
from pathlib import Path

import streamlit as st

from src.graph import build_graph
from src.ingestion import extract_markdown, extract_pdf

logging.basicConfig(level=logging.INFO)
st.set_page_config(page_title="M&A Compliance Reviewer", layout="wide")
st.title("M&A Compliance Reviewer")
st.caption("Synthetic prototype: conservative, evidence-backed review with human approval.")

@st.cache_resource
def get_graph():
    return build_graph()

def run_review(name, documents, use_llm):
    text = "\n\n".join(doc.page_content for doc in documents)
    pages = [{"page": doc.metadata.get("page"), "source": doc.metadata.get("source")} for doc in documents]
    with st.spinner("Running extraction, policy retrieval, compliance, risk, and summary agents..."):
        state = get_graph().invoke({"document_text": text, "document_pages": pages, "use_llm": use_llm})
    st.session_state["review"] = state["result"]
    st.session_state["review_error"] = state.get("error", "")
    st.session_state["review_name"] = name

with st.sidebar:
    st.header("Input")
    upload = st.file_uploader("Upload an M&A PDF", type=["pdf"])
    st.caption("For development, synthetic Markdown deal files are available below.")
    sample = st.selectbox("Or review a sample", ["None"] + [p.name for p in Path("dataset/deals").glob("*.md")])
    use_llm = st.checkbox("Use Ollama deep analysis (slower)", value=False, help="Leave off for an immediate conservative review. Enable for model-generated summaries and findings.")
    if st.button("Run review", type="primary", disabled=not upload and sample == "None"):
        docs = extract_pdf(upload) if upload else extract_markdown(Path("dataset/deals") / sample)
        run_review(upload.name if upload else sample, docs, use_llm)

review = st.session_state.get("review")
if not review:
    st.info("Upload a PDF or select a synthetic sample to begin.")
    st.stop()

st.subheader(f"Review: {st.session_state.get('review_name', 'document')}")
if st.session_state.get("review_error"):
    st.warning("Ollama deep analysis failed, so the app displayed the conservative fallback review. See the terminal for the underlying error.")
status = review.get("overall_status", "needs_review").replace("_", " ").title()
st.metric("Overall status", status)
st.subheader("Summary")
st.write(review.get("summary", "No summary returned."))

if review.get("key_facts"):
    st.subheader("Key facts")
    for fact in review["key_facts"]:
        st.write(f"- {fact}")

st.subheader("Compliance and risk findings")
st.caption("Ambiguous or missing evidence is intentionally routed to human review.")
for index, finding in enumerate(review.get("findings", [])):
    with st.expander(f"{finding['status'].upper()} · {finding['severity'].upper()} · {finding['rule_id']}", expanded=True):
        st.write(finding["explanation"])
        st.markdown(f"**Risk category:** {finding['risk_category']}")
        st.markdown(f"**Document evidence:** {finding['document_evidence']}")
        st.markdown(f"**Citation:** {finding['document_citation']}")
        st.markdown(f"**Policy evidence:** {finding['policy_evidence']}")
        st.markdown(f"**Recommended action:** {finding['recommended_action']}")
        decision = st.selectbox("Reviewer decision", ["pending", "approved", "rejected"], index=["pending", "approved", "rejected"].index(finding.get("reviewer_decision", "pending")), key=f"decision-{index}")
        comment = st.text_area("Reviewer comment", value=finding.get("reviewer_comment", ""), key=f"comment-{index}")
        finding["reviewer_decision"] = decision
        finding["reviewer_comment"] = comment

if st.button("Save review annotations"):
    st.session_state["review"] = review
    st.success("Annotations saved for this session.")

with st.expander("Retrieved policies"):
    for policy in review.get("retrieved_policies", []):
        st.write(f"- {policy}")
