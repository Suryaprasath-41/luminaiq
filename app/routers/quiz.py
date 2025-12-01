from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json
import uuid
from app.database import get_db
from app.models.user import User
from app.models.book import Book, Chapter
from app.schemas.quiz import (
    QuizRequest, QuizResponse, QuizQuestion,
    AnswerQuizSubmission, MCQQuizSubmission, QuizEvaluationResponse, QuestionEvaluation
)
from app.utils.auth import get_current_user
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService

router = APIRouter(prefix="/quiz", tags=["Quiz"])


def parse_quiz_response(response: str) -> List[dict]:
    """Parse LLM response to extract questions"""
    try:
        # Try to find JSON in the response
        start = response.find('{')
        end = response.rfind('}') + 1
        if start != -1 and end > start:
            json_str = response[start:end]
            data = json.loads(json_str)
            return data.get("questions", [])
    except json.JSONDecodeError:
        pass
    
    # If JSON parsing fails, try to find array
    try:
        start = response.find('[')
        end = response.rfind(']') + 1
        if start != -1 and end > start:
            return json.loads(response[start:end])
    except json.JSONDecodeError:
        pass
    
    return []


@router.post("/generate", response_model=QuizResponse)
def generate_quiz(
    request: QuizRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a quiz (MCQ or Answer type) from book/chapter content"""
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
    
    # Initialize services
    rag_service = RAGService()
    llm_service = LLMService()
    
    # Use MMR search for quiz generation to get diverse content coverage
    relevant_docs = rag_service.retrieve(
        query=f"important concepts topics key points {chapter_title or book.title}",
        user_id=current_user.u_id,
        book_id=request.book_id,
        chapter_id=request.chapter_id,
        retrieval_type="mmr",
        top_k=10
    )
    
    if not relevant_docs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No content found to generate quiz"
        )
    
    # Build context
    context = "\n\n".join([doc['content'] for doc in relevant_docs])
    
    # Generate questions
    response = llm_service.generate_questions(
        context=context,
        num_questions=request.num_questions,
        quiz_type=request.quiz_type,
        topic=chapter_title
    )
    
    # Parse response
    questions_data = parse_quiz_response(response)
    
    if not questions_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate quiz questions"
        )
    
    # Convert to QuizQuestion objects
    questions = []
    for i, q in enumerate(questions_data[:request.num_questions], 1):
        questions.append(QuizQuestion(
            question_number=q.get("question_number", i),
            question=q.get("question", ""),
            options=q.get("options") if request.quiz_type == "mcq" else None,
            correct_answer=q.get("correct_answer", "")
        ))
    
    return QuizResponse(
        quiz_id=str(uuid.uuid4()),
        quiz_type=request.quiz_type,
        questions=questions,
        total_questions=len(questions)
    )


@router.post("/evaluate/answer", response_model=QuizEvaluationResponse)
def evaluate_answer_quiz(
    submission: AnswerQuizSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Evaluate answer-type quiz submissions"""
    llm_service = LLMService()
    
    evaluations = []
    total_score = 0.0
    
    for answer in submission.answers:
        # Evaluate each answer
        eval_response = llm_service.evaluate_answer(
            question=answer.question,
            user_answer=answer.user_answer,
            correct_answer=answer.correct_answer
        )
        
        # Parse evaluation response
        try:
            start = eval_response.find('{')
            end = eval_response.rfind('}') + 1
            if start != -1 and end > start:
                eval_data = json.loads(eval_response[start:end])
                score = float(eval_data.get("score", 0))
                feedback = eval_data.get("feedback", "No feedback available")
            else:
                score = 0.0
                feedback = "Could not evaluate this answer"
        except (json.JSONDecodeError, ValueError):
            score = 0.0
            feedback = "Evaluation failed"
        
        total_score += score
        
        evaluations.append(QuestionEvaluation(
            question_number=answer.question_number,
            question=answer.question,
            user_answer=answer.user_answer,
            correct_answer=answer.correct_answer,
            score=score,
            feedback=feedback
        ))
    
    max_score = len(submission.answers)
    percentage = (total_score / max_score * 100) if max_score > 0 else 0
    
    # Generate overall feedback
    if percentage >= 80:
        overall = "Excellent work! You have a strong understanding of the material."
    elif percentage >= 60:
        overall = "Good effort! Review the topics where you lost points."
    elif percentage >= 40:
        overall = "You're making progress. Focus on reviewing the material more thoroughly."
    else:
        overall = "Keep practicing! Consider re-reading the chapters and trying again."
    
    return QuizEvaluationResponse(
        quiz_id=submission.quiz_id,
        total_score=total_score,
        max_score=float(max_score),
        percentage=percentage,
        evaluations=evaluations,
        overall_feedback=overall
    )


@router.post("/evaluate/mcq", response_model=QuizEvaluationResponse)
def evaluate_mcq_quiz(
    submission: MCQQuizSubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Evaluate MCQ quiz submissions"""
    evaluations = []
    total_score = 0.0
    
    for answer in submission.answers:
        # Check if selected option matches correct answer
        is_correct = answer.selected_option.strip().lower() == answer.correct_answer.strip().lower()
        score = 1.0 if is_correct else 0.0
        total_score += score
        
        feedback = "Correct!" if is_correct else f"Incorrect. The correct answer was: {answer.correct_answer}"
        
        evaluations.append(QuestionEvaluation(
            question_number=answer.question_number,
            question="",  # MCQ questions not stored in submission
            user_answer=answer.selected_option,
            correct_answer=answer.correct_answer,
            score=score,
            feedback=feedback
        ))
    
    max_score = len(submission.answers)
    percentage = (total_score / max_score * 100) if max_score > 0 else 0
    
    if percentage >= 80:
        overall = "Excellent work! You have a strong understanding of the material."
    elif percentage >= 60:
        overall = "Good effort! Review the questions you got wrong."
    elif percentage >= 40:
        overall = "You're making progress. Review the material and try again."
    else:
        overall = "Keep practicing! Re-read the chapters and try the quiz again."
    
    return QuizEvaluationResponse(
        quiz_id=submission.quiz_id,
        total_score=total_score,
        max_score=float(max_score),
        percentage=percentage,
        evaluations=evaluations,
        overall_feedback=overall
    )
