from pydantic import BaseModel
from typing import List, Dict, Optional

class Message(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str

class MCPContext(BaseModel):
    user: Dict[str, str]
    history: List[Message]
    instructions: Optional[str] = ""
    report: Optional[str] = None
