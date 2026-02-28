from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_code, routes_compare, routes_chat
from app.core.config import settings


app = FastAPI(
    title="AI Code Intelligence Suite - Hackathon Backend",
    version="0.1.0",
)

# 🔥 ADD THIS BLOCK
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print(f"Gemini API Key Loaded: {bool(settings.gemini_api_key)}")

@app.get("/health", tags=["system"])
def health_check() -> dict:
    return {"status": "ok", "environment": settings.env}


app.include_router(routes_code.router, prefix="/code", tags=["code"])
app.include_router(routes_compare.router, prefix="/compare", tags=["compare"])
app.include_router(routes_chat.router, tags=["chat"])