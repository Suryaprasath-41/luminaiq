from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class QuizQuestion(BaseModel):
    question_number: int
    question: str
    options: Optional[List[str]] = None  # For MCQ
    correct_answer: str


class QuizRequest(BaseModel):
    book_id: int
    chapter_id: Optional[int] = None
    quiz_type: Literal["mcq", "answer"]
    num_questions: Literal[10, 20, 25] = 10


class QuizResponse(BaseModel):
    quiz_id: str
    quiz_type: str
    questions: List[QuizQuestion]
    total_questions: int


class AnswerSubmission(BaseModel):
    question_number: int
    question: str
    user_answer: str
    correct_answer: str


class AnswerQuizSubmission(BaseModel):
    quiz_id: str
    answers: List[AnswerSubmission]


class MCQAnswer(BaseModel):
    question_number: int
    selected_option: str
    correct_answer: str


class MCQQuizSubmission(BaseModel):
    quiz_id: str
    answers: List[MCQAnswer]


class QuestionEvaluation(BaseModel):
    question_number: int
    question: str
    user_answer: str
    correct_answer: str
    score: float
    feedback: str


class QuizEvaluationResponse(BaseModel):
    quiz_id: str
    total_score: float
    max_score: float
    percentage: float
    evaluations: List[QuestionEvaluation]
    overall_feedback: str
