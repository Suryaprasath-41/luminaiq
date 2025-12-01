from app.schemas.user import UserCreate, UserLogin, UserResponse, Token
from app.schemas.book import BookCreate, BookResponse, ChapterCreate, ChapterResponse
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.quiz import (
    QuizRequest, QuizResponse, QuizQuestion,
    AnswerQuizSubmission, MCQQuizSubmission, QuizEvaluationResponse
)
from app.schemas.notes import NotesRequest, NotesResponse
