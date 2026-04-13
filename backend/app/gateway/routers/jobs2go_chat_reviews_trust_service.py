"""Chat, reviews, and trust service interfaces for Jobs2Go pilot."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from app.gateway.routers.jobs2go_offers_service import offers_bookings_store


@dataclass
class MessageRecord:
    id: str
    chat_id: str
    sender_id: str
    message_type: str
    body: str | None
    attachment_url: str | None
    moderation_status: str
    created_at: datetime


@dataclass
class ReviewRecord:
    id: str
    booking_id: str
    reviewer_id: str
    reviewee_id: str
    rating: int
    comment: str | None
    created_at: datetime


@dataclass
class TrustReportRecord:
    id: str
    target_user_id: str
    job_id: str | None
    reason_code: str
    description: str | None
    status: str
    created_at: datetime


class InMemoryChatReviewsTrustStore:
    def __init__(self, booking_store=None) -> None:
        self._messages_by_chat_id: dict[str, list[MessageRecord]] = {}
        self._reviews_by_id: dict[str, ReviewRecord] = {}
        self._reports_by_id: dict[str, TrustReportRecord] = {}
        self._booking_store = booking_store or offers_bookings_store

    async def list_messages(self, chat_id: str) -> list[MessageRecord]:
        return self._messages_by_chat_id.get(chat_id, [])

    async def send_message(
        self,
        chat_id: str,
        sender_id: str,
        message_type: str,
        body: str | None,
        attachment_url: str | None,
    ) -> MessageRecord:
        if message_type not in {"text", "image", "video"}:
            raise ValueError("invalid_message_type")
        if message_type == "text" and (body is None or not body.strip()):
            raise ValueError("empty_message")

        moderation_status = _moderate_message(body)
        message = MessageRecord(
            id=str(uuid4()),
            chat_id=chat_id,
            sender_id=sender_id,
            message_type=message_type,
            body=body,
            attachment_url=attachment_url,
            moderation_status=moderation_status,
            created_at=datetime.now(UTC),
        )
        self._messages_by_chat_id.setdefault(chat_id, []).append(message)
        return message

    async def create_review(
        self,
        booking_id: str,
        reviewer_id: str,
        reviewee_id: str,
        rating: int,
        comment: str | None,
    ) -> ReviewRecord:
        if rating < 1 or rating > 5:
            raise ValueError("invalid_rating")

        booking = await self._booking_store.get_booking_by_id(booking_id)
        if booking is None:
            raise ValueError("booking_not_found")

        review = ReviewRecord(
            id=str(uuid4()),
            booking_id=booking_id,
            reviewer_id=reviewer_id,
            reviewee_id=reviewee_id,
            rating=rating,
            comment=comment,
            created_at=datetime.now(UTC),
        )
        self._reviews_by_id[review.id] = review
        return review

    async def submit_report(
        self,
        target_user_id: str,
        job_id: str | None,
        reason_code: str,
        description: str | None,
    ) -> TrustReportRecord:
        if not reason_code.strip():
            raise ValueError("invalid_reason_code")

        status = "priority" if reason_code in {"harassment", "fraud", "identity_theft"} else "queued"
        report = TrustReportRecord(
            id=str(uuid4()),
            target_user_id=target_user_id,
            job_id=job_id,
            reason_code=reason_code,
            description=description,
            status=status,
            created_at=datetime.now(UTC),
        )
        self._reports_by_id[report.id] = report
        return report

    async def list_reviews(self) -> list[ReviewRecord]:
        return list(self._reviews_by_id.values())

    async def list_reports(self) -> list[TrustReportRecord]:
        return list(self._reports_by_id.values())

    def reset(self) -> None:
        self._messages_by_chat_id.clear()
        self._reviews_by_id.clear()
        self._reports_by_id.clear()


def _moderate_message(body: str | None) -> str:
    if body is None:
        return "clear"

    lowered = body.lower()
    blocked_terms = ["pay outside", "off-platform", "cash only"]
    flagged_terms = ["contact me directly", "send number"]

    if any(term in lowered for term in blocked_terms):
        return "blocked"
    if any(term in lowered for term in flagged_terms):
        return "flagged"
    return "clear"


chat_reviews_trust_store = InMemoryChatReviewsTrustStore()
