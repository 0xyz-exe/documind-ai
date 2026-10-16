from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./documind.db"
    
    # Storage
    storage_dir: str = "./storage"
    index_dir: str = "./indexes"
    
    # Embeddings
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_device: str = "cpu"
    
    # Chunking
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    # Retrieval
    top_k: int = 5
    similarity_threshold: float = 0.5
    
    # LLM
    llm_provider: str = "demo"
    llm_api_key: str = ""
    llm_api_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4"
    llm_max_tokens: int = 1000
    llm_temperature: float = 0.1
    
    # Server
    backend_port: int = 8000
    allowed_origins: str = "http://localhost:3000"
    
    # Security
    secret_key: str = "change-me-in-production"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
