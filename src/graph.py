import json
import logging
from typing import TypedDict

from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph

from .config import OLLAMA_BASE_URL, OLLAMA_CHAT_MODEL, USE_LLM_ANALYSIS
from .models import Finding, ReviewResult
from .policies import get_policy_retriever

logger = logging.getLogger(__name__)

class ReviewState(TypedDict, total=False):
    document_text: str
    document_pages: list[dict]
    use_llm: bool
    policies: list[dict]
    result: dict
    error: str

def _llm():
    return ChatOllama(model=OLLAMA_CHAT_MODEL, base_url=OLLAMA_BASE_URL, temperature=0, num_ctx=3072, num_predict=350, timeout=600, keep_alive="5m")

def extraction_node(state: ReviewState) -> ReviewState:
    logger.info("extraction_node")
    return state

def retrieval_node(state: ReviewState) -> ReviewState:
    logger.info("retrieval_node")
    retriever = get_policy_retriever()
    docs = retriever.search(state["document_text"][:1600])
    state["policies"] = [{"content": d.page_content, "metadata": d.metadata} for d in docs]
    return state

def _fallback_review(state: ReviewState) -> dict:
    text = state["document_text"].lower()
    findings = []
    checks = [
        ("SANCTIONS-1", "SANCTIONS", "regulatory", "high", "screen", "Confirm that the target, sellers, beneficial owners, lenders, and intermediaries were screened."),
        ("DATA-PRIVACY-1", "DATA-PRIVACY", "privacy", "medium", "lawful basis", "Document purpose, data categories, recipients, retention, and lawful basis."),
        ("CONFLICTS-1", "CONFLICTS", "reputational", "high", "conflict", "Obtain conflict disclosures and Conflicts Committee review where applicable."),
        ("ANTI-BRIBERY-2", "ANTI-BRIBERY", "legal", "high", "success fee", "Obtain Compliance review and intermediary due diligence."),
    ]
    for rule, policy, category, severity, trigger, action in checks:
        if trigger in text:
            status = "needs_review" if any(word in text for word in ["no ", "not ", "absent", "missing", "does not"]) else "pass"
            findings.append(Finding(rule_id=rule, policy_id=policy, policy_title=policy, status=status, risk_category=category, severity=severity, explanation=f"The document contains language related to {trigger}. The available evidence should be reviewed against the applicable policy before the transaction proceeds.", document_evidence="See the relevant wording in the uploaded document.", document_citation="Document text; precise page citation is unavailable in fast review mode.", policy_evidence="Applicable policy was retrieved from the indexed library.", recommended_action=action).model_dump())
    summary = "Synthetic M&A review completed using the conservative fallback evaluator. Connect Ollama for model-based analysis."
    return ReviewResult(summary=summary, overall_status="needs_review" if findings else "pass", key_facts=[], findings=findings, retrieved_policies=[p["metadata"].get("title", "Unknown") for p in state.get("policies", [])]).model_dump()

def analysis_node(state: ReviewState) -> ReviewState:
    logger.info("analysis_node")
    if not state.get("use_llm", USE_LLM_ANALYSIS):
        state["result"] = _fallback_review(state)
        return state
    policy_text = "\n\n".join(p["content"] for p in state.get("policies", []))
    prompt = f"""Review this M&A document against the supplied policies. Be conservative: missing or ambiguous evidence must be needs_review, never pass. Return only the structured review object.
Use page numbers in document_citation when available. Risk categories: legal, financial, regulatory, operational, privacy, reputational.
DOCUMENT:\n{state['document_text'][:6000]}\nPOLICIES:\n{policy_text[:7000]}"""
    try:
        response = _llm().with_structured_output(ReviewResult).invoke(prompt)
        parsed = response.model_dump() if isinstance(response, ReviewResult) else response
        parsed.setdefault("retrieved_policies", [p["metadata"].get("title", "Unknown") for p in state.get("policies", [])])
        validated = ReviewResult.model_validate(parsed).model_dump()
        # Small local models may return a valid empty findings array even when
        # the document contains obvious review topics. Never show a blank
        # compliance section in that case; preserve the model summary and use
        # the conservative evaluator to populate actionable findings.
        if not validated["findings"]:
            fallback = _fallback_review(state)
            validated["findings"] = fallback["findings"]
            validated["overall_status"] = "needs_review" if fallback["findings"] else validated["overall_status"]
        state["result"] = validated
    except Exception as exc:
        logger.warning("Ollama analysis failed; using conservative fallback: %s", exc)
        state["error"] = str(exc)
        state["result"] = _fallback_review(state)
    return state

def build_graph():
    graph = StateGraph(ReviewState)
    graph.add_node("extract", extraction_node)
    graph.add_node("retrieve_policies", retrieval_node)
    graph.add_node("analyze", analysis_node)
    graph.set_entry_point("extract")
    graph.add_edge("extract", "retrieve_policies")
    graph.add_edge("retrieve_policies", "analyze")
    graph.add_edge("analyze", END)
    return graph.compile()
