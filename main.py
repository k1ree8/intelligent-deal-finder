from fastapi import FastAPI
from src.api.endpoints import router as ads_router

app = FastAPI(
    title="Intelligent Deal Finder",
    description="API for smart search of profitable offers on Avito",
    version="0.1.0",
)

app.include_router(ads_router, prefix="/api/v1")


@app.get("/")
def read_root():
    """
    Root endpoint that returns a welcome message.
    """
    return {"message": "Welcome to the Intelligent Deal Finder API!"}
