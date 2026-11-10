from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import models  # noqa: F401  (registers the tables on Base.metadata)
from app.db import Base, engine


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Fine for local development. Switch to migrations (Alembic) before real data.
    Base.metadata.create_all(engine)
    yield


app = FastAPI(
    title="Paid on Time API",
    description="Cash forecasting and compliance checks for NYC-contracted nonprofits.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
