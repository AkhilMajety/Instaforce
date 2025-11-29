from typing import Dict, Any
from src.llm.model import LLMModel
from src.state.state import State


class BaseAgentNode:
    def __init__(self, model: LLMModel):
        self.llm = model


def process(self, state: State) -> Dict[str, Any]:
    raise NotImplementedError