from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.book import Book
from app.schemas.chat import ChatRequest, ChatResponse
from app.utils.auth import get_current_user
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Chat with the learning assistant using RAG"""
    # Validate book if provided
    if request.book_id:
        book = db.query(Book).filter(
            Book.id == request.book_id,
            Book.user_id == current_user.u_id
        ).first()
        
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found"
            )
    
    # Initialize services
    rag_service = RAGService()
    llm_service = LLMService()
    
    # Retrieve relevant context using appropriate technique
    # Use hybrid search for chat to get diverse and relevant results
    retrieval_type = "hybrid"
    
    if request.chapter_id:
        # For chapter-specific queries, use similarity search for precision
        retrieval_type = "similarity"
    
    relevant_docs = rag_service.retrieve(
        query=request.message,
        user_id=current_user.u_id,
        book_id=request.book_id,
        chapter_id=request.chapter_id,
        retrieval_type=retrieval_type,
        top_k=5
    )
    
    # Build context from retrieved documents
    if relevant_docs:
        context = "\n\n".join([
            f"[From: {doc['chapter_title']}]\n{doc['content']}"
            for doc in relevant_docs
        ])
        sources = list(set([doc['chapter_title'] for doc in relevant_docs]))
    else:
        context = "No relevant content found in your uploaded materials."
        sources = []
    
    # Convert chat history to the format expected by LLM
    history = None
    if request.history:
        history = [{"role": msg.role, "content": msg.content} for msg in request.history]
    
    # Generate response
    response = llm_service.chat_with_context(
        message=request.message,
        context=context,
        history=history
    )
    
    return ChatResponse(
        response=response,
        sources=sources if sources else None
    )
