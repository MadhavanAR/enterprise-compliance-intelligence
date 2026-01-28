# Compare Mode — Demo Checklist

**DEMO/EDUCATION ONLY.** Compare Mode toggles enterprise safety features to show how the system behaves with them OFF vs ON. All flags default to ON (enterprise-safe).

## Prerequisites

- Open the UI, expand the **sidebar**, and find **🔬 Compare Mode (Demo Only)**.
- Use the four checkboxes: **Refusal on Uncertainty**, **Claim Verification**, **Audit Trail**, **Confidence Scoring**.

---

## Test 1: Refusal ON vs OFF

| Step | Refusal on Uncertainty | Query | Expected |
|------|-------------------------|-------|----------|
| 1a   | **ON** (checked)        | "Should AWS be trusted?" | Refusal: "I don't know." |
| 1b   | **OFF** (unchecked)     | "Should AWS be trusted?" | Answer (no refusal). Log: "refusal_disabled (demo mode)". |

---

## Test 2: Claim Verification ON vs OFF

| Step | Claim Verification | Query | Expected |
|------|--------------------|-------|----------|
| 2a   | **ON**             | Factual, e.g. "What compliance certifications does AWS have?" | Answer with strict claims → sources mapping. |
| 2b   | **OFF**            | Same factual query | Answer even if claim-to-source is weak. Log: "claim_verification_disabled". |

---

## Test 3: Audit Trail ON vs OFF

| Step | Audit Trail | Query | Expected |
|------|-------------|-------|----------|
| 3a   | **ON**      | Any | Full response: answer, claims, sources, decision_path, confidence. |
| 3b   | **OFF**     | Any | Minimal: answer, trace_id, question only. |

---

## Test 4: Confidence Scoring ON vs OFF

| Step | Confidence Scoring | Query | Expected |
|------|--------------------|-------|----------|
| 4a   | **ON**             | Factual | Numeric confidence + reason in Audit & Evidence. |
| 4b   | **OFF**            | Factual | Confidence shows "— (disabled)" in Audit & Evidence. |

---

## Safety

- When **any** of the four is OFF, the UI must show: **⚠️ Demo Mode: Safety features disabled for comparison.**
- Default (all ON) must match production: full refusal, claim verification, audit trail, and confidence.
- Router and Policy flags are not in the UI; they remain ON.

---

## Quick Run (CLI)

The engine can be called with `feature_flags` from Python; CLI and `rag.run` use defaults (all enabled) if not passed.

```python
from rag.engine import run_enterprise_query
from rag.feature_flags import FeatureFlags

# All enabled (default)
run_enterprise_query("Should AWS be trusted?")

# Demo: refusal off
ff = FeatureFlags(enable_refusal=False, enable_query_router=True, enable_policy_engine=True,
                  enforce_grounded_answers=True, enforce_claim_to_source=True,
                  enable_confidence=True, enable_audit_trail=True)
run_enterprise_query("Should AWS be trusted?", feature_flags=ff)
```
