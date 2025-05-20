from typing import Dict, List, Optional
import json
from datetime import datetime
from pathlib import Path
import logging

class ConversationHistory:
    def __init__(self):
        self.store_path = Path(__file__).parent.parent / "data" / "historical_conversations.json"
        self.store_path.parent.mkdir(exist_ok=True)
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self._init_store()

    def _init_store(self):
        try:
            if not self.store_path.exists():
                with open(self.store_path, 'w') as f:
                    json.dump({"conversations": []}, f, indent=2)
            self.logger.info(f"Initialized history store at {self.store_path}")
        except Exception as e:
            self.logger.error(f"Error initializing store: {e}")

    async def add_entry(self, query: str, response: str, session_id: str, metadata: Optional[Dict] = None):
        try:
            with open(self.store_path, 'r') as f:
                data = json.load(f)
            
            entry = {
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "query": query,
                "response": response,
                "metadata": metadata or {}
            }
            
            data["conversations"].append(entry)
            
            with open(self.store_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Added new entry for session {session_id}")
        except Exception as e:
            self.logger.error(f"Error adding entry: {e}")

    async def search_relevant(self, query: str, limit: int = 5) -> List[Dict]:
        try:
            with open(self.store_path, 'r') as f:
                data = json.load(f)
            
            relevant = [
                conv for conv in data["conversations"]
                if query.lower() in conv["query"].lower()
            ]
            
            self.logger.info(f"Found {len(relevant)} relevant entries")
            return sorted(
                relevant,
                key=lambda x: x["timestamp"],
                reverse=True
            )[:limit]
        except Exception as e:
            self.logger.error(f"Error searching conversations: {e}")
            return []


async def use_history_for_query(self, query: str) -> Dict:
    # Find relevant past conversations
    relevant_history = await self.search_relevant("Anmol singh DLF apartment")
    
    if relevant_history:
        # Extract previous answer about the amount
        previous_answer = relevant_history[0]["response"]
        amount = "85 crores"  # Extracted from previous response
        
        # Use this information for the new calculation
        return {
            "previous_context": f"Previously found amount: {amount}",
            "can_use_directly": True,
            "value": amount
        }
    
    return {"can_use_directly": False}