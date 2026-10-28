from typing import Literal
from pydantic import BaseModel, Field

Status = Literal["pass", "fail", "needs_review"]
Severity = Literal["low", "medium", "high", "critical"]

class Finding(BaseModel):
    rule_id: str
    policy_id: str
    policy_title: str
    status: Status
    risk_category: str
    severity: Severity
    explanation: str
    document_evidence: str
    document_citation: str
    policy_evidence: str
    recommended_action: str
    reviewer_decision: str = "pending"
    reviewer_comment: str = ""

class ReviewResult(BaseModel):
    summary: str
    overall_status: Status
    key_facts: list[str] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    retrieved_policies: list[str] = Field(default_factory=list)
