from fastapi import FastAPI
from backend.app.api.routes import router  # Use absolute import
from dotenv import load_dotenv
import os
import uvicorn
# from backend.app.core.config import settings
import openai
load_dotenv()

# Print the loaded API key for verification
print("Loaded PINECONE_API_KEY:", os.getenv("PINECONE_API_KEY"))
# openai.api_key = settings.OPENAI_API_KEY
app = FastAPI()

app.include_router(router)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))  # Default to 10000 as per Render's default
    print(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port) 