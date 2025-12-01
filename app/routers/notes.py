from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.book import Book, Chapter
from app.schemas.notes import NotesRequest, NotesResponse
from app.utils.auth import get_current_user
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService

router = APIRouter(prefix="/notes", tags=["Notes"])


@router.post("/generate", response_model=NotesResponse)
def generate_notes(
    request: NotesRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate study notes from book/chapter content"""
    # Validate book
    book = db.query(Book).filter(
        Book.id == request.book_id,
        Book.user_id == current_user.u_id
    ).first()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Get chapter if specified
    chapter_title = None
    chapter_content = None
    
    if request.chapter_id:
        chapter = db.query(Chapter).filter(
            Chapter.id == request.chapter_id,
            Chapter.book_id == request.book_id
        ).first()
        
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chapter not found"
            )
        
        chapter_title = chapter.title
        chapter_content = chapter.content
    
    # Initialize services
    rag_service = RAGService()
    llm_service = LLMService()
    
    # Get content for notes generation
    if chapter_content:
        # Use chapter content directly if available
        content = chapter_content
    else:
        # Use RAG to get comprehensive content
        # Use similarity search for notes to get most relevant content
        relevant_docs = rag_service.retrieve(
            query=f"main concepts definitions explanations examples {chapter_title or book.title}",
            user_id=current_user.u_id,
            book_id=request.book_id,
            chapter_id=request.chapter_id,
            retrieval_type="similarity",
            top_k=15  # Get more content for comprehensive notes
        )
        
        if not relevant_docs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No content found to generate notes"
            )
        
        content = "\n\n".join([doc['content'] for doc in relevant_docs])
    
    # Generate notes
    notes_content = llm_service.generate_notes(
        content=content,
        notes_type=request.notes_type,
        topic=chapter_title
    )
    
    return NotesResponse(
        book_title=book.title,
        chapter_title=chapter_title,
        notes_type=request.notes_type,
        content=notes_content
    )
