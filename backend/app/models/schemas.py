from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

class Repository(BaseModel):
    url: str
    branch: str = "main"
    type: str  # "code" or "docs"

class ProjectSetup(BaseModel):
    code_repo: Repository
    docs_repo: Repository
    
class CodeChunk(BaseModel):
    id: str
    content: str
    file_path: str
    start_line: int
    end_line: int
    embedding: Optional[List[float]] = None
    
class DocChunk(BaseModel):
    id: str
    content: str
    file_path: str
    embedding: Optional[List[float]] = None
    related_code_chunks: List[str] = []

class DocumentationUpdate(BaseModel):
    file_path: str
    original_content: str
    updated_content: str
    related_code_changes: Dict
    timestamp: datetime = datetime.now() 