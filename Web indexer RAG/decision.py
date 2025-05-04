from pydantic import BaseModel
from models import DecisionOutput, PerceptionData, MemoryItem
from typing import List

class Decision:
    def __init__(self):
        self.strategies = {}
        
    def make_decision(self, perceived_data: PerceptionData, memory_data: List[MemoryItem]) -> DecisionOutput:
        """Make decisions based on perceived data and memories"""
        return DecisionOutput(
            action_type="default",
            parameters={},
            confidence=1.0,
            reasoning="Default decision"
        )