from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Documentation Updater"
    API_V1_STR: str = "/api/v1"
    
    # OpenAI
    OPENAI_API_KEY: str
    
    # Vector DB (Pinecone)
    # PINECONE_API_KEY: str
    # PINECONE_ENV: str
    # PINECONE_INDEX: str
    
    class Config:
        env_file = ".env"

settings = Settings() 