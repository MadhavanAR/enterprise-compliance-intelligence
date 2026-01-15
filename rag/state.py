from typing import TypedDict, List, Literal

class RagState(TypedDict):
    question: str
    context: List[str]
    answer: str
    route: Literal["rag", "end"]