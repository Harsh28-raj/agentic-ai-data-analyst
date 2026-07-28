"""
FastAPI Application Entrypoint for DataMind AI Backend.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from core.config import settings
from core.logger import logger
from api.routes import router as api_router

app = FastAPI(
    title="DataMind AI Backend API",
    description="Production-Ready AI-powered Data Analyst REST API powered by Groq Cloud & LangGraph ReAct agent",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
app.include_router(api_router)


@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting DataMind AI Backend (Model: {settings.MODEL_NAME}, Host: {settings.BACKEND_HOST}:{settings.BACKEND_PORT})")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception: {str(exc)} | Path: {request.url.path}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred.", "error": str(exc)}
    )
