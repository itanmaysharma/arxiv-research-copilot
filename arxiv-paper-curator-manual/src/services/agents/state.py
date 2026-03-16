from dataclasses import dataclass, field


@dataclass
class AgentState:
    question: str
    top_k: int
    rewritten_question: str | None = None
    context: str = ""
    sources: list[dict] = field(default_factory=list)
    scope_reason: str = ""
    grade_reason: str = ""
