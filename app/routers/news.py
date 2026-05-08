"""Outbreak Intelligence Feed router."""

import logging

from fastapi import APIRouter, Response

from app.models.response_models import NewsArticle
from app.services import news_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/news", response_model=list[NewsArticle])
async def get_news(response: Response) -> list[NewsArticle]:
    """Return the current outbreak headline list with a 60-second cache hint."""
    response.headers["Cache-Control"] = "max-age=60"
    return await news_service.fetch_headlines()


@router.get("/news/refresh", response_model=list[NewsArticle])
async def refresh_news(response: Response) -> list[NewsArticle]:
    """Force-refresh the headline list, instructing clients not to cache."""
    response.headers["Cache-Control"] = "no-cache"
    return await news_service.fetch_headlines()
