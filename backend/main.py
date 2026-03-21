from fastapi import FastAPI

from backend.api.routes import router

app = FastAPI(
    title="Figma Automation Pipeline",
    description="AI-powered pipeline that converts product intent into structured UI screens",
    version="0.1.0",
)

app.include_router(router)
