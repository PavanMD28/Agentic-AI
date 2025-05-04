from pydantic import BaseModel
from perception import Perception
from memory import Memory
from decision import Decision
from action import Action
from models import PerceptionData, ActionResult

class Agent:
    def __init__(self):
        self.perception = Perception()
        self.memory = Memory()
        self.decision = Decision()
        self.action = Action()
        
    def process_input(self, input_data: Any) -> ActionResult:
        # Process input through the agent components
        perceived_data = self.perception.process(input_data)
        memory_data = self.memory.retrieve(perceived_data)
        decision = self.decision.make_decision(perceived_data, memory_data)
        result = self.action.execute(decision)
        return result