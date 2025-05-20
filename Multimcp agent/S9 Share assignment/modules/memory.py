# modules/memory.py

import json
import os
import time
from typing import List, Optional, Dict, Any  # Added Dict to imports
from pydantic import BaseModel
import uuid
from datetime import datetime as dt

# Optional fallback logger
try:
    from agent import log
except ImportError:
    import datetime
    def log(stage: str, msg: str):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{now}] [{stage}] {msg}")

class MemoryItem(BaseModel):
    """Represents a single memory entry for a session."""
    timestamp: float
    type: str  # run_metadata, tool_call, tool_output, final_answer
    text: str
    tool_name: Optional[str] = None
    tool_args: Optional[dict] = None
    tool_result: Optional[dict] = None
    final_answer: Optional[str] = None
    tags: Optional[List[str]] = []
    success: Optional[bool] = None
    metadata: Optional[dict] = {}  # ✅ ADD THIS LINE BACK


class MemoryManager:
    """Manages session memory (read/write/append)."""

    def __init__(self, session_id: str, memory_dir: str = "memory"):
        self.session_id = session_id
        self.memory_dir = memory_dir
        self.memory_path = os.path.join('memory', session_id.split('-')[0], session_id.split('-')[1], session_id.split('-')[2], f'session-{session_id}.json')
        self.items: List[MemoryItem] = []
        self.history_file = 'data/historical_conversations.json'
        os.makedirs('data', exist_ok=True)

        if not os.path.exists(self.memory_dir):
            os.makedirs(self.memory_dir)

        self.load()

    def load(self):
        if os.path.exists(self.memory_path):
            with open(self.memory_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
                self.items = [MemoryItem(**item) for item in raw]
        else:
            self.items = []

    def save(self):
        # Before opening the file for writing
        os.makedirs(os.path.dirname(self.memory_path), exist_ok=True)
        with open(self.memory_path, "w", encoding="utf-8") as f:
            raw = [item.dict() for item in self.items]
            json.dump(raw, f, indent=2)

    def add(self, item: MemoryItem):
        self.items.append(item)
        self.save()

    def add_tool_call(
        self, tool_name: str, tool_args: dict, tags: Optional[List[str]] = None
    ):
        item = MemoryItem(
            timestamp=time.time(),
            type="tool_call",
            text=f"Called {tool_name} with {tool_args}",
            tool_name=tool_name,
            tool_args=tool_args,
            tags=tags or [],
        )
        self.add(item)

    def add_tool_output(self, tool_name: str, tool_args: dict, tool_result: dict, success: bool = True, tags: Optional[List[str]] = None):
        """Add tool execution output to memory"""
        item = MemoryItem(
            timestamp=time.time(),
            type="tool_output",
            text=f"Output of {tool_name}: {tool_result}",
            tool_name=tool_name,
            tool_args=tool_args,
            tool_result=tool_result,
            success=success,
            tags=tags or []
        )
        self.add(item)
        
        # Also save to conversation history
        self.save_conversation(
            query=f"Tool execution: {tool_name}",
            response=f"Arguments: {tool_args}\nResult: {tool_result}"
        )

    def save_conversation(self, query: str, response: str):
        """Save a conversation to the historical data file"""
        timestamp = dt.now().isoformat()
        
        conversation = {
            "timestamp": timestamp,
            "session_id": self.session_id,
            "query": query,
            "response": response,
            "metadata": {
                "timestamp": timestamp,
                "type": "final"
            }
        }
        
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                data = json.load(f)
        else:
            data = {"conversations": []}
            
        data["conversations"].append(conversation)
        with open(self.history_file, 'w') as f:
            json.dump(data, f, indent=2)

    def get_session_items(self) -> List[MemoryItem]:
        """Return all memory items for current session."""
        return self.items

    def get_session_items(self) -> List[MemoryItem]:
        """
        Return all memory items for current session.
        """
        if os.path.exists(self.history_file):
            with open(self.history_file, 'r') as f:
                data = json.load(f)
                conversations = data.get("conversations", [])
                return [
                    MemoryItem(
                        timestamp=time.time(),  # Use time.time() instead of ISO string
                        text=f"Q: {conv['query']}\nA: {conv['response']}",
                        type="conversation",
                        metadata={
                            "original_timestamp": conv["timestamp"],
                            "session_id": conv["session_id"]
                        }
                    )
                    for conv in conversations
                    if conv["session_id"] == self.session_id
                ]
        return []
