from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.user import User
from app.models.book import Book, Chapter
from app.schemas.book import BookCreate, BookResponse, ChapterResponse, BookUploadResponse
from app.utils.auth import get_current_user
from app.services.document_service import DocumentService
from app.services.rag_service import RAGService

router = APIRouter(prefix="/books", tags=["Books"])


@router.post("/upload", response_model=BookUploadResponse)
async def upload_book(
    file: UploadFile = File(...),
    title: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a PDF/DOCX file and process it as a book"""
    # Validate file type
    allowed_types = ['.pdf', '.docx', '.txt']
    file_ext = '.' + file.filename.split('.')[-1].lower()
    
    if file_ext not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not supported. Allowed types: {allowed_types}"
        )
    
    # Read file content
    content = await file.read()
    
    # Extract text
    doc_service = DocumentService()
    try:
        text = doc_service.extract_text(content, file.filename)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error extracting text: {str(e)}"
        )
    
    # Detect chapters
    chapters_data = doc_service.detect_chapters(text)
    
    # Create book record
    book = Book(title=title, user_id=current_user.u_id)
    db.add(book)
    db.commit()
    db.refresh(book)
    
    # Create chapters and store in RAG
    rag_service = RAGService()
    
    for chapter_data in chapters_data:
        chapter = Chapter(
            book_id=book.id,
            title=chapter_data["title"],
            chapter_number=chapter_data["chapter_number"],
            content=chapter_data["content"]
        )
        db.add(chapter)
        db.commit()
        db.refresh(chapter)
        
        # Store in RAG
        if chapter_data["content"]:
            rag_service.store_document(
                user_id=current_user.u_id,
                book_id=book.id,
                chapter_id=chapter.id,
                chapter_title=chapter.title,
                content=chapter_data["content"]
            )
    
    return BookUploadResponse(
        id=book.id,
        title=book.title,
        chapters_count=len(chapters_data),
        message="Book uploaded and processed successfully"
    )


@router.get("/", response_model=List[BookResponse])
def get_books(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all books for current user"""
    books = db.query(Book).filter(Book.user_id == current_user.u_id).all()
    return books


@router.get("/{book_id}", response_model=BookResponse)
def get_book(
    book_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific book"""
    book = db.query(Book).filter(
        Book.id == book_id,
        Book.user_id == current_user.u_id
    ).first()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    return book


@router.get("/{book_id}/chapters", response_model=List[ChapterResponse])
def get_chapters(
    book_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all chapters of a book"""
    book = db.query(Book).filter(
        Book.id == book_id,
        Book.user_id == current_user.u_id
    ).first()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    return book.chapters


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(
    book_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a book and its RAG data"""
    book = db.query(Book).filter(
        Book.id == book_id,
        Book.user_id == current_user.u_id
    ).first()
    
    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found"
        )
    
    # Delete from RAG
    rag_service = RAGService()
    rag_service.delete_book_documents(current_user.u_id, book_id)
    
    # Delete from database
    db.delete(book)
    db.commit()
