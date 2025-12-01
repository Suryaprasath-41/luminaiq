from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routers import auth_router, books_router, chat_router, quiz_router, notes_router

app = FastAPI(
    title="LuminaIQ Learning API",
    description="A comprehensive learning platform backend with RAG-powered features",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(books_router)
app.include_router(chat_router)
app.include_router(quiz_router)
app.include_router(notes_router)


@app.on_event("startup")
def startup_event():
    """Initialize database on startup"""
    init_db()


@app.get("/")
def root():
    return {
        "message": "Welcome to LuminaIQ Learning API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
