"""
DEMO-ONLY Compare Mode: Feature flags to toggle enterprise safety features.

- All flags default to True (enterprise-safe).
- Only the engine reads feature flags; downstream modules receive them via state.
- Never production-default off; for education and comparison only.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class FeatureFlags:
    enable_query_router: bool = True
    enable_policy_engine: bool = True
    enforce_grounded_answers: bool = True
    enforce_claim_to_source: bool = True
    enable_refusal: bool = True
    enable_confidence: bool = True
    enable_audit_trail: bool = True
