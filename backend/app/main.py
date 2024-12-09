from fastapi import FastAPI
from backend.app.api.routes import router  # Use absolute import

app = FastAPI()

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000) 