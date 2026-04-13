"""Router for Jobs2Go chat, reviews, and trust endpoints."""

from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.gateway.routers.jobs2go_chat_reviews_trust_service import chat_reviews_trust_store
from app.gateway.routers.jobs2go_common import Jobs2GoModuleStatus

router = APIRouter(prefix="/v1", tags=["jobs2go-chat-reviews-trust"])


class MessageResponse(BaseModel):
    id: str
    chat_id: str
    sender_id: str
    message_type: str
    body: str | None
    attachment_url: str | None
    moderation_status: str
    created_at: datetime


class MessageListResponse(BaseModel):
    items: list[MessageResponse]


class SendMessageRequest(BaseModel):
    sender_id: str
    message_type: str = Field(pattern="^(text|image|video)$")
    body: str | None = None
    attachment_url: str | None = None


class ReviewCreateRequest(BaseModel):
    booking_id: str
    reviewer_id: str
    reviewee_id: str
    rating: int = Field(ge=1, le=5)
    comment: str | None = None


class ReviewResponse(BaseModel):
    id: str
    booking_id: str
    reviewer_id: str
    reviewee_id: str
    rating: int
    comment: str | None
    created_at: datetime


class TrustReportRequest(BaseModel):
    target_user_id: str
    job_id: str | None = None
    reason_code: str
    description: str | None = None


class TrustReportResponse(BaseModel):
    id: str
    target_user_id: str
    job_id: str | None
    reason_code: str
    description: str | None
    status: str
    created_at: datetime


@router.get("/chats/_status", response_model=Jobs2GoModuleStatus)
async def chats_status() -> Jobs2GoModuleStatus:
    """Status endpoint for chat module readiness."""
    return Jobs2GoModuleStatus(
        module="chat",
        status="active",
        next_step="Add realtime transport layer in Step 11",
    )


@router.get("/chats/{chatId}/messages", response_model=MessageListResponse)
async def list_messages(chatId: str) -> MessageListResponse:
    """List messages for a chat."""
    items = await chat_reviews_trust_store.list_messages(chatId)
    return MessageListResponse(items=[MessageResponse(**item.__dict__) for item in items])


@router.post("/chats/{chatId}/messages", response_model=MessageResponse, status_code=201)
async def send_message(chatId: str, payload: SendMessageRequest) -> MessageResponse:
    """Send a message to a chat with basic moderation checks."""
    try:
        message = await chat_reviews_trust_store.send_message(
            chat_id=chatId,
            sender_id=payload.sender_id,
            message_type=payload.message_type,
            body=payload.body,
            attachment_url=payload.attachment_url,
        )
    except ValueError as exc:
        if str(exc) == "invalid_message_type":
            raise HTTPException(status_code=400, detail="Invalid message type") from exc
        if str(exc) == "empty_message":
            raise HTTPException(status_code=400, detail="Text message body is required") from exc
        raise

    return MessageResponse(**message.__dict__)


@router.get("/reviews/_status", response_model=Jobs2GoModuleStatus)
async def reviews_status() -> Jobs2GoModuleStatus:
    """Status endpoint for reviews module readiness."""
    return Jobs2GoModuleStatus(
        module="reviews",
        status="active",
        next_step="Add anti-fraud review integrity scoring in Step 12",
    )


@router.post("/reviews", response_model=ReviewResponse, status_code=201)
async def create_review(payload: ReviewCreateRequest) -> ReviewResponse:
    """Submit a review for a completed booking."""
    try:
        review = await chat_reviews_trust_store.create_review(
            booking_id=payload.booking_id,
            reviewer_id=payload.reviewer_id,
            reviewee_id=payload.reviewee_id,
            rating=payload.rating,
            comment=payload.comment,
        )
    except ValueError as exc:
        if str(exc) == "invalid_rating":
            raise HTTPException(status_code=400, detail="Rating must be between 1 and 5") from exc
        if str(exc) == "booking_not_found":
            raise HTTPException(status_code=404, detail="Booking not found") from exc
        raise

    return ReviewResponse(**review.__dict__)


@router.get("/trust/_status", response_model=Jobs2GoModuleStatus)
async def trust_status() -> Jobs2GoModuleStatus:
    """Status endpoint for trust module readiness."""
    return Jobs2GoModuleStatus(
        module="trust",
        status="active",
        next_step="Add sanction workflows in Step 12",
    )


@router.post("/trust/reports", response_model=TrustReportResponse, status_code=201)
async def submit_trust_report(payload: TrustReportRequest) -> TrustReportResponse:
    """Submit abuse or fraud report for trust and safety review."""
    try:
        report = await chat_reviews_trust_store.submit_report(
            target_user_id=payload.target_user_id,
            job_id=payload.job_id,
            reason_code=payload.reason_code,
            description=payload.description,
        )
    except ValueError as exc:
        if str(exc) == "invalid_reason_code":
            raise HTTPException(status_code=400, detail="Reason code is required") from exc
        raise

    return TrustReportResponse(**report.__dict__)
