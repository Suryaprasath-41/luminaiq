from pydantic import BaseModel
from typing import Optional, Literal


class NotesRequest(BaseModel):
    book_id: int
    chapter_id: Optional[int] = None
    notes_type: Literal["comprehensive", "explanatory"] = "comprehensive"


class NotesResponse(BaseModel):
    book_title: str
    chapter_title: Optional[str] = None
    notes_type: str
    content: str
