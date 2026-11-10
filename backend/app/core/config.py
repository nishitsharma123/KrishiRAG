import os
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "KrishiRAG"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    DEBUG: bool = True

    HOST: str = "127.0.0.1"
    PORT: int = 8000

    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    @field_validator("CORS_ORIGINS", mode="after")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            # Check if JSON array string
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    # Database
    DATABASE_URL: str = "sqlite:///./data/krishirag.db"

    # Storage Paths
    QDRANT_STORAGE_PATH: str = "./data/qdrant_db"
    QDRANT_COLLECTION_NAME: str = "icar_agricultural_knowledge"
    RAW_DATA_PATH: str = "./data/raw"
    PROCESSED_DATA_PATH: str = "./data/processed"
    STORAGE_PATH: str = "./storage"

    # Ingestion & Chunking
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".txt", ".docx"]
    SCAN_TEXT_THRESHOLD: int = 50
    CHUNK_MIN_TOKENS: int = 500
    CHUNK_MAX_TOKENS: int = 700
    CHUNK_OVERLAP_TOKENS: int = 80

    # Embedding & Retrieval
    EMBEDDING_MODEL_NAME: str = "intfloat/multilingual-e5-small"
    RERANKER_MODEL_NAME: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    EMBEDDING_BATCH_SIZE: int = 8
    TOP_K_DENSE: int = 6
    TOP_K_SPARSE: int = 6
    FINAL_CONTEXT_CHUNKS: int = 2

    # LLM Settings
    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "qwen3:4b"
    OLLAMA_CONTEXT_WINDOW: int = 1536
    OLLAMA_NUM_THREADS: int = 6
    LLM_TIMEOUT_SECONDS: int = 70

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
