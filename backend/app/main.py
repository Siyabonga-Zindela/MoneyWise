"""FastAPI application entry point."""

from fastapi import FastAPI

from .routes.analysis import router as analysis_router


app = FastAPI(title="MoneyWise API")
app.include_router(analysis_router)
