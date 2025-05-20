# core/context.py

from typing import List, Optional, Dict, Any
from modules.memory import MemoryManager, MemoryItem
from core.session import MultiMCP  # For dispatcher typing
from pathlib import Path
import yaml
import time
import uuid
from datetime import datetime as dt  # Change the import at the top
from pydantic import BaseModel

class StrategyProfile(BaseModel):
    planning_mode: str
    exploration_mode: Optional[str] = None
    memory_fallback_enabled: bool
    max_steps: int
    max_lifelines_per_step: int


class AgentProfile:
    def __init__(self):
        with open("config/profiles.yaml", "r") as f:
            config = yaml.safe_load(f)

        self.name = config["agent"]["name"]
        self.id = config["agent"]["id"]
        self.description = config["agent"]["description"]

        self.strategy = StrategyProfile(**config["strategy"])
        self.memory_config = config["memory"]
        self.llm_config = config["llm"]
        self.persona = config["persona"]


    def __repr__(self):
        return f"<AgentProfile {self.name} ({self.strategy})>"

class AgentContext:
    """Holds all session state, user input, memory, and strategies."""

    def __init__(
        self,
        user_input: str,
        session_id: Optional[str] = None,
        dispatcher: Optional[Any] = None,
        mcp_server_descriptions: Optional[Dict] = None,
    ):
        # Generate session_id first if None
        self.session_id = session_id if session_id else str(uuid.uuid4())
        self.user_input = user_input
        self.dispatcher = dispatcher
        self.mcp_server_descriptions = mcp_server_descriptions or {}
        self.available_servers = list(self.mcp_server_descriptions.keys()) if self.mcp_server_descriptions else []
        self.agent_profile = AgentProfile()
        
        # Initialize memory with the guaranteed non-None session_id
        self.memory = MemoryManager(session_id=self.session_id)
        
        # Remove duplicate assignment
        # self.session_id = self.memory.session_id  # Remove this line
        
        self.step = 0
        self.task_progress = []
        self.final_answer = None
        self.tool_calls = []  # Initialize tool_calls list
        self.dispatcher = dispatcher  # 🆕 Added formally
        self.mcp_server_descriptions = mcp_server_descriptions  # 🆕 Added formally
        self.step = 0
        self.task_progress = []  # 🆕 Will track tool executions
        self.final_answer = None
        

        # Log session start
        self.add_memory(MemoryItem(
            timestamp=time.time(),
            text=f"Started new session with input: {user_input} at {dt.utcnow().isoformat()}",  # Use dt instead of datetime
            type="run_metadata",
            session_id=self.session_id,
            tags=["run_start"],
            user_query=user_input,
            metadata={
                "start_time": dt.now().isoformat(),  # Use dt instead of datetime
                "step": self.step
            }
        ))

    def add_memory(self, item: MemoryItem):
        """Add item to memory"""
        if isinstance(item, dict) and "result" in item:
            # If it's a final answer, save to historical conversations
            if "FINAL_ANSWER:" in item["result"]:
                self.memory.save_conversation(
                    query=self.user_input,
                    response=item["result"]  # Save complete response including results
                )
        # Store the memory item directly without using a non-existent method
        if isinstance(item, MemoryItem):
            memory_dict = {
                "timestamp": dt.now().isoformat(),  # Use dt instead of datetime
                "text": getattr(item, 'text', ''),
                "type": getattr(item, 'type', 'unknown'),
                "tags": getattr(item, 'tags', []),
                "user_query": getattr(item, 'user_query', ''),
                "metadata": getattr(item, 'metadata', {})
            }
            self.memory.save_conversation(
                query=self.user_input,
                response=memory_dict["text"]
            )

    def format_history_for_llm(self) -> str:
        if not self.tool_calls:
            return "No previous actions"
            
        history = []
        for i, trace in enumerate(self.tool_calls, 1):
            result_str = str(trace.result)
            if i < len(self.tool_calls):  # Previous steps
                if len(result_str) > 50:
                    result_str = f"{result_str[:50]}... [RESPONSE TRUNCATED]"
            # else: last step gets full result
            
            history.append(f"{i}. Used {trace.tool_name} with {trace.arguments}\nResult: {result_str}")
        
        return "\n\n".join(history)

    def log_subtask(self, tool_name: str, status: str = "pending"):
        """Log the start of a new subtask."""
        self.task_progress.append({
            "step": self.step,
            "tool": tool_name,
            "status": status,
        })

    def update_subtask_status(self, tool_name: str, status: str):
        """Update the status of an existing subtask."""
        for item in reversed(self.task_progress):
            if item["tool"] == tool_name and item["step"] == self.step:
                item["status"] = status
                break

    def __repr__(self):
        return f"<AgentContext step={self.step}, session_id={self.session_id}>"
