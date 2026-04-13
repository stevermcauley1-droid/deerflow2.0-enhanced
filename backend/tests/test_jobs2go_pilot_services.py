import asyncio

import pytest

from app.gateway.routers.jobs2go_chat_reviews_trust_service import chat_reviews_trust_store
from app.gateway.routers.jobs2go_jobs_service import create_job_record, jobs_store
from app.gateway.routers.jobs2go_offers_service import offers_bookings_store
from app.gateway.routers.jobs2go_ops import get_kpi_snapshot
from app.gateway.routers.jobs2go_payments_service import payments_store


@pytest.fixture(autouse=True)
def reset_jobs2go_stores():
    jobs_store.reset()
    offers_bookings_store.reset()
    payments_store.reset()
    chat_reviews_trust_store.reset()
    yield
    jobs_store.reset()
    offers_bookings_store.reset()
    payments_store.reset()
    chat_reviews_trust_store.reset()


def test_jobs2go_full_payment_lifecycle_happy_path():
    async def _run():
        job = create_job_record(
            {
                "employer_id": "emp_1",
                "title": "Assemble wardrobe",
                "description": "Need assembly done this afternoon",
                "category_code": "home_services.furniture_assembly",
                "location_mode": "onsite",
                "budget_type": "hourly",
                "budget_min_cents": 5000,
                "budget_max_cents": 7000,
                "currency": "USD",
            }
        )
        await jobs_store.create_job(job)

        offer = await offers_bookings_store.create_offer(
            job_id=job.id,
            worker_id="w_1",
            message="Can you start now?",
            proposed_amount_cents=12000,
            currency="USD",
            expires_at=None,
        )
        accepted = await offers_bookings_store.accept_offer(offer.id)
        assert accepted.status == "accepted"

        started = await offers_bookings_store.start_job(job.id)
        assert started.status == "in_progress"

        completed = await offers_bookings_store.complete_job(job.id, "Completed successfully")
        assert completed.status == "completed"

        authorized = await payments_store.authorize_escrow(
            booking_id=completed.id,
            payment_method_id="pm_demo",
            amount_cents=12000,
            currency="USD",
        )
        assert authorized.escrow_status == "authorized"
        assert authorized.gross_amount_cents == authorized.platform_fee_cents + authorized.worker_payout_cents

        released = await payments_store.release_escrow(booking_id=completed.id)
        assert released.escrow_status == "released"

    asyncio.run(_run())


def test_escrow_release_requires_completed_booking():
    async def _run():
        job = create_job_record(
            {
                "employer_id": "emp_2",
                "title": "Quick cleaning",
                "description": "Kitchen cleaning",
                "category_code": "home_services.cleaning",
                "location_mode": "onsite",
                "currency": "USD",
            }
        )
        await jobs_store.create_job(job)

        offer = await offers_bookings_store.create_offer(
            job_id=job.id,
            worker_id="w_2",
            message=None,
            proposed_amount_cents=8000,
            currency="USD",
            expires_at=None,
        )
        await offers_bookings_store.accept_offer(offer.id)
        booking = await offers_bookings_store.get_booking_by_job_id(job.id)
        assert booking is not None

        await payments_store.authorize_escrow(
            booking_id=booking.id,
            payment_method_id="pm_demo",
            amount_cents=8000,
            currency="USD",
        )

        with pytest.raises(ValueError, match="booking_not_completed"):
            await payments_store.release_escrow(booking_id=booking.id)

    asyncio.run(_run())


def test_message_moderation_review_and_trust_priority():
    async def _run():
        msg = await chat_reviews_trust_store.send_message(
            chat_id="chat_1",
            sender_id="w_1",
            message_type="text",
            body="Can we do cash only and pay outside the app?",
            attachment_url=None,
        )
        assert msg.moderation_status == "blocked"

        job = create_job_record(
            {
                "employer_id": "emp_3",
                "title": "Move boxes",
                "description": "2-hour task",
                "category_code": "general.task",
                "location_mode": "onsite",
                "currency": "USD",
            }
        )
        await jobs_store.create_job(job)
        offer = await offers_bookings_store.create_offer(
            job_id=job.id,
            worker_id="w_3",
            message=None,
            proposed_amount_cents=6000,
            currency="USD",
            expires_at=None,
        )
        await offers_bookings_store.accept_offer(offer.id)
        await offers_bookings_store.complete_job(job.id, "done")
        booking = await offers_bookings_store.get_booking_by_job_id(job.id)
        assert booking is not None

        review = await chat_reviews_trust_store.create_review(
            booking_id=booking.id,
            reviewer_id="emp_3",
            reviewee_id="w_3",
            rating=5,
            comment="Great work",
        )
        assert review.rating == 5

        report = await chat_reviews_trust_store.submit_report(
            target_user_id="w_3",
            job_id=job.id,
            reason_code="fraud",
            description="Suspicious behavior",
        )
        assert report.status == "priority"

    asyncio.run(_run())


def test_ops_kpi_snapshot_counts():
    async def _run():
        job = create_job_record(
            {
                "employer_id": "emp_4",
                "title": "Fix shelf",
                "description": "Need repair",
                "category_code": "home_services.furniture_assembly",
                "location_mode": "onsite",
                "currency": "USD",
            }
        )
        await jobs_store.create_job(job)

        offer = await offers_bookings_store.create_offer(
            job_id=job.id,
            worker_id="w_1",
            message=None,
            proposed_amount_cents=9000,
            currency="USD",
            expires_at=None,
        )
        await offers_bookings_store.accept_offer(offer.id)
        await offers_bookings_store.complete_job(job.id, "done")
        booking = await offers_bookings_store.get_booking_by_job_id(job.id)
        assert booking is not None

        await payments_store.authorize_escrow(
            booking_id=booking.id,
            payment_method_id="pm_demo",
            amount_cents=9000,
            currency="USD",
        )
        await payments_store.release_escrow(booking_id=booking.id)

        await chat_reviews_trust_store.create_review(
            booking_id=booking.id,
            reviewer_id="emp_4",
            reviewee_id="w_1",
            rating=4,
            comment=None,
        )
        await chat_reviews_trust_store.submit_report(
            target_user_id="w_1",
            job_id=job.id,
            reason_code="harassment",
            description="Demo report",
        )

        snapshot = await get_kpi_snapshot()
        assert snapshot.jobs_created == 1
        assert snapshot.offers_sent == 1
        assert snapshot.offers_accepted == 1
        assert snapshot.bookings_completed == 1
        assert snapshot.escrow_authorized_count == 1
        assert snapshot.escrow_released_count == 1
        assert snapshot.reviews_count == 1
        assert snapshot.trust_reports_count == 1
        assert snapshot.trust_priority_reports_count == 1

    asyncio.run(_run())
