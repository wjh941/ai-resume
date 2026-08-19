from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.schemas.common import success
from app.schemas.job_collections import FavoriteJobCreate, JobSubscriptionUpdate
from app.services.auth import current_user_id


router = APIRouter(prefix="/api/job-collection", tags=["job-collection"])


@router.get("/favorites")
def list_favorites(request: Request, user_id: str = Depends(current_user_id)):
    items = request.app.state.job_collection_repository.list_favorites(user_id)
    return success({"items": [item.as_dict() for item in items]})


@router.post("/favorites")
def save_favorite(payload: FavoriteJobCreate, request: Request, user_id: str = Depends(current_user_id)):
    return success(request.app.state.job_collection_repository.save_favorite(user_id, payload).as_dict())


@router.delete("/favorites/{favorite_id}")
def delete_favorite(favorite_id: str, request: Request, user_id: str = Depends(current_user_id)):
    request.app.state.job_collection_repository.delete_favorite(user_id, favorite_id)
    return success({"id": favorite_id})


@router.get("/subscription")
def get_subscription(request: Request, user_id: str = Depends(current_user_id)):
    return success(request.app.state.job_collection_repository.subscription(user_id).as_dict())


@router.put("/subscription")
def update_subscription(payload: JobSubscriptionUpdate, request: Request, user_id: str = Depends(current_user_id)):
    # TODO: Connect an approved external source and notification channel in a later phase.
    subscription = request.app.state.job_collection_repository.set_subscription(
        user_id, payload.enabled, payload.match_filter
    )
    return success(subscription.as_dict())
