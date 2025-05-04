from pydantic import BaseModel
from models import MemoryItem
import faiss
import numpy as np
from datetime import datetime

class Memory:
    def __init__(self):
        self.index = None
        self.metadata: List[MemoryItem] = []
        
    def store(self, data: Any, embedding: np.ndarray) -> None:
        """Store data and its embedding in memory"""
        memory_item = MemoryItem(
            data=data,
            embedding=embedding.tolist(),
            timestamp=datetime.now()
        )
        
        if self.index is None:
            self.index = faiss.IndexFlatL2(len(embedding))
        self.index.add(embedding.reshape(1, -1))
        self.metadata.append(memory_item)
        
    def retrieve(self, query_data: Any) -> List[MemoryItem]:
        """Retrieve relevant memories based on query"""
        if not self.index:
            return []
        return self.metadata