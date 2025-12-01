from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class ChapterCreate(BaseModel):
    title: str
    chapter_number: int
    content: Optional[str] = None


class ChapterResponse(BaseModel):
    id: int
    title: str
    chapter_number: int
    book_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class BookCreate(BaseModel):
    title: str
    chapters: Optional[List[ChapterCreate]] = None


class BookResponse(BaseModel):
    id: int
    title: str
    user_id: int
    created_at: datetime
    chapters: List[ChapterResponse] = []

    class Config:
        from_attributes = True


class BookUploadResponse(BaseModel):
    id: int
    title: str
    chapters_count: int
    message: str
