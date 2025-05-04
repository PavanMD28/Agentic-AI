from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime

class PerceptionData(BaseModel):
    raw_input: Any
    embeddings: Optional[List[float]] = None
    timestamp: datetime = datetime.now()

class MemoryItem(BaseModel):
    data: Any
    embedding: List[float]
    timestamp: datetime = datetime.now()
    metadata: Dict[str, Any] = {}

class DecisionOutput(BaseModel):
    action_type: str
    parameters: Dict[str, Any]
    confidence: float
    reasoning: str

class ActionResult(BaseModel):
    status: str
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float