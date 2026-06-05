import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import endpoints

app = FastAPI(
    title="MCP Postman AI Runner",
    version="1.0.0",
    description="Run Postman collections and analyse responses with a configurable LLM.",
)

_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
]
_origins += [o.strip() for o in os.getenv("MCP_ALLOWED_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(endpoints.router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "MCP Postman AI Runner is running", "docs": "/docs", "api": "/api/info"}
