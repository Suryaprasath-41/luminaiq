# LuminaIQ Learning Platform

LuminaIQ is a comprehensive AI-powered learning platform that leverages RAG (Retrieval-Augmented Generation) technology to provide personalized educational experiences. The platform enables users to upload documents, engage in intelligent conversations, generate quizzes, evaluate learning progress, and create comprehensive study notes.

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
git clone https://github.com/Suryaprasath-41/luminaiq.git
cd luminaiq
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Setup
Create a `.env` file in the root directory:
```env
TOGETHER_API_KEY=your_together_ai_api_key_here
QDRANT_HOST=localhost
QDRANT_PORT=6333
SECRET_KEY=your_jwt_secret_key
DATABASE_URL=sqlite:///./luminaiq.db
```

### 5. Initialize Database
```bash
python -c "from app.database import init_db; init_db()"
```

### 6. Run the Application
```bash
python run.py
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

Once the server is running, visit:
- **Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

### Main API Endpoints

#### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user info

#### Books Management
- `POST /books/upload` - Upload book document
- `GET /books` - List user's books
- `GET /books/{book_id}` - Get book details
- `DELETE /books/{book_id}` - Delete book

#### Chat
- `POST /chat/` - Chat with AI assistant
- Supports optional `book_id` and `chapter_id` for context

#### Quiz
- `POST /quiz/generate` - Generate quiz questions
- `POST /quiz/evaluate/answer` - Evaluate answer-type quiz
- `POST /quiz/evaluate/mcq` - Evaluate MCQ quiz

#### Notes
- `POST /notes/generate` - Generate study notes

## 🏗️ Project Structure

```
luminaiq/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Application configuration
│   ├── database.py          # Database initialization
│   ├── models/              # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py          # User model
│   │   └── book.py          # Book and Chapter models
│   ├── routers/             # API route handlers
│   │   ├── __init__.py
│   │   ├── auth.py          # Authentication routes
│   │   ├── books.py         # Book management routes
│   │   ├── chat.py          # Chat routes
│   │   ├── quiz.py          # Quiz generation and evaluation
│   │   └── notes.py         # Notes generation routes
│   ├── schemas/             # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py          # User schemas
│   │   ├── book.py          # Book schemas
│   │   ├── chat.py          # Chat schemas
│   │   ├── quiz.py          # Quiz schemas
│   │   └── notes.py         # Notes schemas
│   ├── services/            # Business logic services
│   │   ├── __init__.py
│   │   ├── llm_service.py   # Together AI integration
│   │   ├── rag_service.py   # RAG functionality
│   │   └── document_service.py  # Document processing
│   └── utils/               # Utility functions
│       ├── __init__.py
│       └── auth.py          # Authentication utilities
├── run.py                   # Application runner
├── requirements.txt         # Python dependencies
├── .env                     # Environment variables (create this)
└── README.md                # This file
```

## 🔧 Configuration

### RAG Retrieval Techniques

The platform uses different retrieval techniques for optimal performance:

- **Similarity Search**: For precise chapter-specific queries
- **Hybrid Search**: For diverse and relevant chat results
- **MMR (Maximal Marginal Relevance)**: For comprehensive quiz generation

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TOGETHER_API_KEY` | API key for Together AI services | Yes |
| `QDRANT_HOST` | Qdrant vector database host | Yes |
| `QDRANT_PORT` | Qdrant vector database port | Yes |
| `SECRET_KEY` | JWT secret key for authentication | Yes |
| `DATABASE_URL` | SQLite database URL | Yes |

## 📖 Usage Examples

### 1. User Registration
```bash
curl -X POST "http://localhost:8000/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"username": "student1", "password": "securepass123"}'
```

### 2. Upload Book
```bash
curl -X POST "http://localhost:8000/books/upload" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -F "file=@textbook.pdf"
```

### 3. Generate Quiz
```bash
curl -X POST "http://localhost:8000/quiz/generate" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "book_id": "uuid-here",
       "quiz_type": "mcq",
       "num_questions": 20
     }'
```

### 4. Chat with AI
```bash
curl -X POST "http://localhost:8000/chat/" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "message": "Explain the main concept of this chapter",
       "book_id": "uuid-here"
     }'
```

## 🧪 Testing

Run the health check endpoint to verify the system is working:

```bash
curl http://localhost:8000/health
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🐛 Troubleshooting

### Common Issues

1. **Database Connection Error**: Ensure SQLite database is properly initialized
2. **RAG Service Error**: Check Qdrant connection and Together AI API key
3. **Document Upload Fails**: Verify file format (PDF/DOCX) and size limits

### Support

For issues and questions, please create an issue in the GitHub repository.

## 🔮 Future Enhancements

- [ ] Frontend web application
- [ ] Mobile app support
- [ ] Advanced analytics dashboard
- [ ] Collaborative learning features
- [ ] Offline mode support
- [ ] Multi-language support
- [ ] Integration with learning management systems

---

**Built with ❤️ for empowering education through AI**