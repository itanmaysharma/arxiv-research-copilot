from src.schemas.agentic import AgenticStep
from src.services.agents.nodes.generate import run_generate
from src.services.agents.nodes.grade_documents_node import run_grade_documents
from src.services.agents.nodes.guardrail import run_guardrail
from src.services.agents.nodes.out_of_scope_node import run_out_of_scope
from src.services.agents.nodes.retrieve import run_retrieve
from src.services.agents.nodes.rewrite import run_rewrite
from src.services.agents.state import AgentState


def run_agentic_workflow(question: str, top_k: int):
    state = AgentState(question=question, top_k=top_k)
    steps: list[AgenticStep] = []

    allowed, guardrail_msg = run_guardrail(question)
    steps.append(AgenticStep(node="guardrail", status="ok" if allowed else "blocked", detail=guardrail_msg))
    if not allowed:
        return "Question blocked by guardrail.", steps, []

    is_out, scope_msg = run_out_of_scope(question)
    steps.append(AgenticStep(node="out_of_scope", status="blocked" if is_out else "ok", detail=scope_msg))
    if is_out:
        return "Question is out of scope for this research assistant.", steps, []

    context, sources = run_retrieve(question, top_k, min_score=2.0)
    state.context = context
    state.sources = sources

    if context:
        steps.append(AgenticStep(node="retrieve", status="ok", detail=f"Retrieved {len(sources)} chunks"))
    else:
        steps.append(AgenticStep(node="retrieve", status="empty", detail="No relevant context found"))
        rewritten = run_rewrite(question)
        state.rewritten_question = rewritten
        steps.append(AgenticStep(node="rewrite", status="ok", detail=f"Rewrote query to: {rewritten}"))

        context, sources = run_retrieve(rewritten, top_k, min_score=2.0)
        state.context = context
        state.sources = sources
        if not context:
            steps.append(AgenticStep(node="retrieve_retry", status="empty", detail="No context after rewrite"))
            return "I could not find relevant context, even after query rewriting.", steps, []

        steps.append(AgenticStep(node="retrieve_retry", status="ok", detail=f"Retrieved {len(sources)} chunks"))

    grade_ok, grade_msg = run_grade_documents(question=question, sources=state.sources)
    state.grade_reason = grade_msg
    steps.append(AgenticStep(node="grade_documents", status="ok" if grade_ok else "reject", detail=grade_msg))
    if not grade_ok:
        return "Retrieved documents were not relevant enough to answer confidently.", steps, []

    answer = run_generate(question, state.context)
    steps.append(AgenticStep(node="generate", status="ok", detail="Generated answer"))

    return answer, steps, state.sources
