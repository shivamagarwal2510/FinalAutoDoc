from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.routes import router  # Use absolute import
from dotenv import load_dotenv
import os
import uvicorn
# from backend.app.core.config import settings
import openai
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Print the loaded API key for verification
logger.info("Loaded PINECONE_API_KEY: %s", os.getenv("PINECONE_API_KEY"))
# openai.api_key = settings.OPENAI_API_KEY
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add a root route
@app.get("/")
async def root():
    return {"message": "Welcome to AutoDocs API"}

app.include_router(router)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = "0.0.0.0"
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    ) 