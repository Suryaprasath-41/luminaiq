from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    together_api_key: str = ""
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str = ""
    jwt_secret_key: str = "change-this-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    database_url: str = "sqlite:///./luminaiq.db"
    
    # Model configurations
    llm_model: str = "meta-llama/Llama-3.3-70B-Instruct-Turbo"
    embedding_model: str = "BAAI/bge-base-en-v1.5"
    embedding_dimension: int = 768

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache()
def get_settings():
    return Settings()
