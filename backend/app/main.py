"""Application entry point.

This file creates the FastAPI application and defines the most basic routes.
Everything else in the project will eventually plug into the `app` object
created here.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run setup before the app serves traffic, and cleanup after it stops.

    The schema is NOT created here any more. Alembic owns it, so deploys run
    `alembic upgrade head` before starting the app. An application that
    silently reshapes its own database on boot is a bad idea in production.
    """
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Turn your PDF notes into summaries, quizzes, and flashcards.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Tells the browser which origins may read responses from this API.
# allow_origins is an explicit list, never ["*"], because "*" would let any
# website on the internet call this API with a user's credentials.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def read_root():
    """Confirm the API is reachable."""
    return {"message": "AI Study Assistant API is running"}


@app.get("/health")
def health_check():
    """Report service health.

    Hosting platforms like Render call this endpoint on a schedule. If it
    stops returning 200 OK, they know the service is unhealthy and restart it.
    """
    return {"status": "ok"}
