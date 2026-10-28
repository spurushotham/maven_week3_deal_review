# Synthetic M&A Review Dataset

This dataset supports the M&A compliance-review prototype. It is fictional and contains no real companies, people, or transactions.

## Contents

- `deals/`: synthetic transaction documents. These are Markdown source documents that can be rendered to PDF for Streamlit upload testing.
- `policies/`: versioned policy documents for indexing and retrieval.
- `evaluation/ground_truth.jsonl`: labeled compliance and risk cases.
- `policy_catalog.json`: policy metadata used for version selection.

## Intended labels

- `pass`: evidence satisfies the applicable policy.
- `fail`: evidence conflicts with a policy requirement.
- `needs_review`: required information is missing, ambiguous, or jurisdiction-dependent.

Risk categories are legal, financial, regulatory, operational, privacy, and reputational.

## Suggested evaluation split

- `deal_meridian`: baseline compliant transaction with one missing approval artifact.
- `deal_northstar`: intentional sanctions, privacy, and approval violations.
- `deal_orion`: ambiguous cross-border and related-party issues.
- `deal_lattice`: mostly compliant transaction with a stale-policy/versioning trap.
