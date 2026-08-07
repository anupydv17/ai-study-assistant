"""Collects every v1 endpoint group into one router.

main.py includes this single router, so adding a new feature means adding one
line here rather than editing the application entry point.
"""

from fastapi import APIRouter

from app.api.v1 import auth, documents, history, study, users

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(documents.router)
api_router.include_router(study.router)
api_router.include_router(history.router)
