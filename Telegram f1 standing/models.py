from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class Driver(BaseModel):
    position: str
    driver_name: str
    points: str

class F1Standings(BaseModel):
    timestamp: datetime
    standings: List[Driver]
    season: str = "2024"
    last_updated: Optional[datetime] = None
    analysis: Optional[str] = None

class MessageContext(BaseModel):
    message_id: str
    message_type: str
    content: F1Standings
    source: str = "F1_API"
    timestamp: datetime = datetime.now()
    metadata: Dict = {}

    class Config:
        arbitrary_types_allowed = True