from rag.state import RagState
from rag.logger import get_logger
from rag.query_router import route_query
from rag.policy_engine import evaluate_policies, check_post_generation_policy
from rag.feature_flags import FeatureFlags

# Phase 1 supervisor (keep for backward compatibility)
def supervisor_node(state: RagState):
    q = state["question"].lower()

    # simple routing logic (LLM-free for now)
    if any(k in q for k in ["explain", "what is", "how", "why"]):
        return {"route": "rag"}
    
    return {"route": "rag"}  # default

# Phase 3 supervisor (formalized multi-agent supervisor with Query Router)
from langgraph.graph import StateGraph, END
from rag.research_team import build_research_graph
from rag.writing_team import build_writing_graph
from rag.state import AgentState

research_app = build_research_graph()
writing_app = build_writing_graph()

def supervisor_node_phase3(state: AgentState):
    """
    Supervisor node with Query Router, observability, and explicit state management.
    
    ENTERPRISE-GRADE:
    - Query Router: Intent classification, routing decision, metadata extraction
    - Explicit Agent State: trace_id, decision_path, used_tools, metadata_filters
    - Grounded Answer: Structured claims + citations
    - Confidence Scoring: Risk level estimation
    """
    trace_id = state.get("trace_id")
    logger = get_logger(trace_id)
    
    # Ensure trace_id is set
    if not trace_id:
        import uuid
        trace_id = str(uuid.uuid4())
        state["trace_id"] = trace_id
    
    question = state.get("question", "")
    ff = state.get("feature_flags") or FeatureFlags()

    # QUERY ROUTER: Intent classification and routing decision (skip if disabled for demo)
    if ff.enable_query_router:
        logger.info("Query Router: Analyzing query intent", query_preview=question[:50])
        routing_decision = route_query(question, trace_id=trace_id)
        use_rag = routing_decision.get("use_rag", True)
        use_web = routing_decision.get("use_web", False)
        refuse = routing_decision.get("refuse", False)
        intent = routing_decision.get("intent", "unknown")
        confidence_requirement = routing_decision.get("confidence_requirement", "medium")
        routing_metadata_filters = routing_decision.get("metadata_filters")
        decision_path = ["query_router"]
    else:
        logger.info("Query Router: Skipped (demo mode)", decision_path="router_skipped")
        use_rag = True
        use_web = False
        refuse = False
        intent = "factual"
        confidence_requirement = "medium"
        routing_metadata_filters = None
        routing_decision = {"use_rag": True, "use_web": False, "refuse": False, "intent": "factual", "metadata_filters": None, "confidence_requirement": "medium"}
        decision_path = ["router_skipped"]

    if routing_metadata_filters:
        existing_filters = state.get("metadata_filters", {}) or {}
        metadata_filters = {**existing_filters, **routing_metadata_filters}
    else:
        metadata_filters = state.get("metadata_filters")

    if ff.enable_query_router:
        logger.info("Query Router: Decision complete",
                    intent=intent, use_rag=use_rag, use_web=use_web, refuse=refuse,
                    metadata_filters=metadata_filters, confidence_requirement=confidence_requirement)

    # POLICY ENGINE: Evaluate policies BEFORE retrieval (skip if disabled for demo)
    if ff.enable_policy_engine:
        policy_result = evaluate_policies(
            intent=intent,
            confidence_requirement=confidence_requirement,
            metadata_filters=metadata_filters,
            trace_id=trace_id
        )
        logger.info("Policy Engine: Policies evaluated",
                    allowed=policy_result.get("allowed", True), refuse=policy_result.get("refuse", False),
                    confidence_threshold=policy_result.get("confidence_threshold", 0.5),
                    violations_count=len(policy_result.get("policy_violations", [])))
    else:
        logger.info("Policy Engine: Skipped (demo mode)", decision_path="policy_skipped")
        policy_result = {"allowed": True, "refuse": False, "reason": None, "confidence_threshold": 0.5, "refuse_on_low_confidence": False, "policy_violations": []}

    state["policy_result"] = policy_result
    policy_allowed = policy_result.get("allowed", True)
    policy_refuse = policy_result.get("refuse", False)
    policy_reason = policy_result.get("reason")
    confidence_threshold = policy_result.get("confidence_threshold", 0.5)
    refuse_on_low_confidence = policy_result.get("refuse_on_low_confidence", False)
    policy_violations = policy_result.get("policy_violations", [])
    if policy_violations:
        decision_path.append("policy_check")

    if not ff.enable_refusal and (refuse or not policy_allowed or policy_refuse):
        logger.info("Refusal bypassed (demo mode)", reason="refusal_disabled (demo mode)")

    # HARD REFUSAL: If router OR policy says refuse, return immediately (skip if refusal disabled for demo)
    if ff.enable_refusal and (refuse or not policy_allowed or policy_refuse):
        refusal_reason = policy_reason or "Query refused: opinion/speculation detected by router"
        logger.warning("Query refused", reason=refusal_reason, policy_violations=policy_violations)
        
        decision_path.append("refuse")
        
        return {
            "answer": "I don't know.",
            "claims": [],
            "sources_used": [],
            "confidence": 0.0,
            "confidence_reason": refusal_reason,
            "trace_id": trace_id,
            "decision_path": decision_path,
            "used_tools": [],
            "metadata_filters": metadata_filters,
            "intent": intent,
            "policy_violations": policy_violations
        }
    
    # Update state with routing decision and metadata filters
    state["metadata_filters"] = metadata_filters
    state["routing_decision"] = routing_decision
    
    # Determine decision path
    if use_web:
        decision_path = ["query_router", "web_search"]
    elif use_rag:
        decision_path = ["query_router", "rag"]
    else:
        decision_path = ["query_router", "unknown"]
    
    logger.info(f"Supervisor: Routing to Research Team (path: {' -> '.join(decision_path)})")
    logger.start_timer("supervisor_research")
    
    research_result = research_app.invoke(state)
    
    # Extract decision path and tools from research result
    research_decision_path = research_result.get("decision_path", "rag")
    used_tools = research_result.get("used_tools", [])
    
    # Update decision path with research result
    decision_path.append(research_decision_path)
    
    logger.end_timer("supervisor_research",
                    research_notes_count=len(research_result.get("research_notes", [])),
                    tool_calls_count=len(research_result.get("tool_calls", [])),
                    decision_path=" -> ".join(decision_path))
    
    logger.info("Supervisor: Routing to Writing Team", decision_path=" -> ".join(decision_path))
    logger.start_timer("supervisor_writing")
    
    writing_result = writing_app.invoke(research_result)
    
    # Extract structured response (get all fields from writing_result)
    answer = writing_result.get("answer", "")
    claims = writing_result.get("claims", [])
    sources_used = writing_result.get("sources_used", [])
    confidence = writing_result.get("confidence", 0.5)
    confidence_reason = writing_result.get("confidence_reason", "")
    
    # POLICY ENGINE: Post-generation policy check (skip if policy disabled for demo)
    if ff.enable_policy_engine:
        _conf = confidence if confidence is not None else 0.0
        post_policy_result = check_post_generation_policy(
            confidence=_conf,
            confidence_threshold=confidence_threshold,
            refuse_on_low_confidence=refuse_on_low_confidence,
            trace_id=trace_id
        )
    else:
        post_policy_result = {"refuse": False}

    if not ff.enable_refusal and post_policy_result.get("refuse") and post_policy_result.get("reason"):
        logger.info("Post-generation refusal bypassed (demo mode)", reason="refusal_disabled (demo mode)")

    # Enforce post-generation policy if enabled (skip when refusal disabled for demo)
    if ff.enable_refusal and post_policy_result.get("refuse") and post_policy_result.get("reason"):
        logger.warning("Post-generation policy violation", 
                      reason=post_policy_result.get("reason"),
                      confidence=confidence,
                      threshold=confidence_threshold)
        decision_path.append("policy_refuse")
        answer = "I don't know."
        claims = []
        sources_used = []
        confidence_reason = post_policy_result.get("reason") or confidence_reason
    
    logger.end_timer("supervisor_writing",
                    answer_length=len(answer),
                    claims_count=len(claims),
                    confidence=confidence)
    
    # ENTERPRISE-GRADE: Structured final response
    # Merge writing_result first, then add supervisor fields (ensures all fields are included)
    final_result = {
        **writing_result,  # Include all fields from writing_result (answer, claims, sources_used, confidence, etc.)
        "trace_id": trace_id,
        "decision_path": decision_path,  # List of decision points (includes policy checks)
        "used_tools": used_tools,
        "metadata_filters": metadata_filters,
        "intent": intent,
        "confidence_requirement": confidence_requirement
    }
    
    # Update answer/claims if post-generation policy refused
    if post_policy_result.get("refuse"):
        final_result["answer"] = answer
        final_result["claims"] = claims
        final_result["sources_used"] = sources_used
        final_result["confidence_reason"] = confidence_reason
    
    # Ensure required fields exist (defensive)
    if "answer" not in final_result:
        final_result["answer"] = answer
    if "claims" not in final_result:
        final_result["claims"] = claims
    if "sources_used" not in final_result:
        final_result["sources_used"] = sources_used
    if "confidence" not in final_result:
        final_result["confidence"] = confidence
    if "confidence_reason" not in final_result:
        final_result["confidence_reason"] = confidence_reason
    
    logger.info("Supervisor: Complete", 
                final_answer_length=len(answer),
                claims_count=len(claims),
                sources_count=len(sources_used),
                confidence=confidence,
                decision_path=" -> ".join(decision_path),
                intent=intent)
    
    return final_result

def build_supervisor():
    graph = StateGraph(AgentState)
    graph.add_node("supervisor", supervisor_node_phase3)
    graph.set_entry_point("supervisor")
    graph.add_edge("supervisor", END)
    return graph.compile()
