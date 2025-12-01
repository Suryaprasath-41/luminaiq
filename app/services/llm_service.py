from together import Together
from typing import List, Dict, Optional
from app.config import get_settings

settings = get_settings()


class LLMService:
    def __init__(self):
        self.client = Together(api_key=settings.together_api_key)
        self.model = settings.llm_model

    def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        max_tokens: int = 2048,
        temperature: float = 0.7
    ) -> str:
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        if history:
            messages.extend(history)
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.choices[0].message.content

    def generate_questions(
        self,
        context: str,
        num_questions: int,
        quiz_type: str,
        topic: Optional[str] = None
    ) -> str:
        if quiz_type == "mcq":
            system_prompt = """You are an expert quiz generator. Generate multiple choice questions based on the provided content.
Each question must have exactly 4 options (A, B, C, D) with only one correct answer.
Format your response as JSON with the following structure:
{
    "questions": [
        {
            "question_number": 1,
            "question": "Question text here?",
            "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
            "correct_answer": "A) Option 1"
        }
    ]
}"""
        else:
            system_prompt = """You are an expert quiz generator. Generate short answer questions based on the provided content.
Format your response as JSON with the following structure:
{
    "questions": [
        {
            "question_number": 1,
            "question": "Question text here?",
            "correct_answer": "Expected answer here"
        }
    ]
}"""

        topic_str = f" focusing on the topic: {topic}" if topic else ""
        prompt = f"""Based on the following content{topic_str}, generate exactly {num_questions} {quiz_type.upper()} questions:

Content:
{context}

Generate the questions in the specified JSON format."""

        return self.generate_response(prompt, system_prompt, temperature=0.5)

    def evaluate_answer(
        self,
        question: str,
        user_answer: str,
        correct_answer: str,
        context: Optional[str] = None
    ) -> Dict:
        system_prompt = """You are an expert evaluator for educational assessments.
Evaluate the student's answer against the correct answer.
Provide a score from 0 to 1 (0 = completely wrong, 1 = completely correct, partial credit allowed).
Also provide brief feedback explaining the evaluation.
Format your response as JSON:
{
    "score": 0.8,
    "feedback": "Your explanation of the feedback here"
}"""

        context_str = f"\nContext for reference:\n{context}" if context else ""
        prompt = f"""Question: {question}
Correct Answer: {correct_answer}
Student's Answer: {user_answer}
{context_str}

Evaluate the student's answer and provide score and feedback in JSON format."""

        return self.generate_response(prompt, system_prompt, temperature=0.3)

    def generate_notes(
        self,
        content: str,
        notes_type: str,
        topic: Optional[str] = None
    ) -> str:
        if notes_type == "comprehensive":
            system_prompt = """You are an expert educator. Generate comprehensive study notes from the provided content.
Include:
- Key concepts and definitions
- Important facts and figures
- Main ideas organized by topic
- Summary points
Make the notes well-structured with clear headings and bullet points."""
        else:
            system_prompt = """You are an expert educator. Generate explanatory study notes from the provided content.
Include:
- Detailed explanations of concepts
- Examples and illustrations
- Step-by-step breakdowns of complex topics
- Connections between different concepts
Make the notes easy to understand with clear explanations."""

        topic_str = f" focusing on: {topic}" if topic else ""
        prompt = f"""Generate {notes_type} notes from the following content{topic_str}:

{content}

Create well-organized and helpful study notes."""

        return self.generate_response(prompt, system_prompt, max_tokens=4096, temperature=0.5)

    def chat_with_context(
        self,
        message: str,
        context: str,
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        system_prompt = """You are a helpful learning assistant. Use the provided context to answer questions accurately.
If the answer cannot be found in the context, say so clearly but try to provide helpful related information.
Be educational and explain concepts thoroughly when asked."""

        prompt = f"""Context from the learning material:
{context}

User's question: {message}

Please provide a helpful and accurate response based on the context."""

        return self.generate_response(prompt, system_prompt, history=history)
