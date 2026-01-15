from typing import TypedDict, List

class RagState(TypedDict):
    question: str
    context: List[str]
    answer: str