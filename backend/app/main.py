from fastapi import FastAPI
from backend.app.api.routes import router  # Use absolute import
from dotenv import load_dotenv
import os
# from backend.app.core.config import settings
import openai
load_dotenv()

# Print the loaded API key for verification
print("Loaded PINECONE_API_KEY:", os.getenv("PINECONE_API_KEY"))
# openai.api_key = settings.OPENAI_API_KEY
app = FastAPI()

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000) 