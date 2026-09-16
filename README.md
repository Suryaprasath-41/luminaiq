# LuminaIQ Learning Platform

LuminaIQ is a comprehensive AI-powered learning platform that leverages RAG (Retrieval-Augmented Generation) technology to provide personalized educational experiences. The platform enables users to upload documents, engage in intelligent conversations, generate quizzes, evaluate learning progress, and create comprehensive study notes.

## 🌐 Live Deployment

The platform is currently deployed and accessible at:
**[https://www.luminaiq.fun](https://www.luminaiq.fun)**

## 🚀 Features

### 1. **Intelligent Chat**
- RAG-powered conversational assistant
- Context-aware responses based on uploaded materials
- Support for book-specific and chapter-specific queries
- Multiple retrieval techniques (similarity, hybrid, MMR)

### 2. **Quiz Generation & Evaluation**
- **Chapter/Topic-wise Quiz Generation**: Create targeted quizzes from specific book chapters
- **Multiple Question Formats**: 
  - MCQ (Multiple Choice Questions)
  - Answer-based questions for detailed evaluation
- **Flexible Question Count**: Generate 10, 20, or 25 questions per quiz
- **Automatic Evaluation**: AI-powered assessment with detailed feedback

### 3. **Smart Notes Generation**
- Generate comprehensive study notes from documents
- Chapter-wise or overall book summaries
- Explanatory and comprehensive format for better understanding
- Structured learning materials for efficient studying

### 4. **User Management**
- Secure user authentication system
- Individual user data isolation
- SQLite database with user management
- Protected API endpoints

### 5. **Document Processing**
- Support for PDF and DOCX file uploads
- Intelligent text extraction and storage
- Chapter identification and organization
- Efficient text-based storage for RAG

## 🛠️ Technology Stack

- **Backend Framework**: FastAPI (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **LLM Integration**: Together AI (GPT-20B for chat, BGE embeddings)
- **Vector Database**: Qdrant for RAG storage and retrieval
- **Authentication**: JWT tokens with bcrypt password hashing
- **Document Processing**: PyPDF, python-docx
- **Server**: Uvicorn ASGI server

## 📋 Prerequisites

- Python 3.8+
- Git
- Together AI API key (will be provided later)

## ⚡ Quick Start

### 1. Clone the Repository
```bash
git clone [https://github.com/Suryaprasath-41/luminaiq.git](https://github.com/Suryaprasath-41/luminaiq.git)
cd luminaiq
