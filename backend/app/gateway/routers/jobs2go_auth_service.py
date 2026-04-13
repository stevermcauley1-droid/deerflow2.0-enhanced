"""Auth and KYC service interfaces for Jobs2Go pilot."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4


@dataclass
class AuthUser:
    id: str
    role: str
    email: str
    phone: str | None
    password_hash: str
    created_at: datetime


@dataclass
class VerificationRecord:
    user_id: str
    kyc_status: str
    background_check_status: str
    updated_at: datetime


class AuthStore(Protocol):
    async def create_user(self, role: str, email: str, phone: str | None, password: str) -> AuthUser:
        ...

    async def get_user_by_email(self, email: str) -> AuthUser | None:
        ...

    async def get_user_by_id(self, user_id: str) -> AuthUser | None:
        ...

    async def get_verification(self, user_id: str) -> VerificationRecord | None:
        ...

    async def set_verification(self, user_id: str, kyc_status: str, background_check_status: str) -> VerificationRecord:
        ...


class KycProvider(Protocol):
    async def start_verification(self, user_id: str) -> str:
        ...


class InMemoryAuthStore(AuthStore):
    def __init__(self) -> None:
        self._users_by_email: dict[str, AuthUser] = {}
        self._users_by_id: dict[str, AuthUser] = {}
        self._verification_by_user_id: dict[str, VerificationRecord] = {}

    async def create_user(self, role: str, email: str, phone: str | None, password: str) -> AuthUser:
        if email in self._users_by_email:
            raise ValueError("email_already_exists")

        user = AuthUser(
            id=str(uuid4()),
            role=role,
            email=email,
            phone=phone,
            password_hash=_hash_password(password),
            created_at=datetime.now(UTC),
        )
        self._users_by_email[email] = user
        self._users_by_id[user.id] = user
        self._verification_by_user_id[user.id] = VerificationRecord(
            user_id=user.id,
            kyc_status="unverified",
            background_check_status="not_requested",
            updated_at=datetime.now(UTC),
        )
        return user

    async def get_user_by_email(self, email: str) -> AuthUser | None:
        return self._users_by_email.get(email)

    async def get_user_by_id(self, user_id: str) -> AuthUser | None:
        return self._users_by_id.get(user_id)

    async def get_verification(self, user_id: str) -> VerificationRecord | None:
        return self._verification_by_user_id.get(user_id)

    async def set_verification(self, user_id: str, kyc_status: str, background_check_status: str) -> VerificationRecord:
        record = VerificationRecord(
            user_id=user_id,
            kyc_status=kyc_status,
            background_check_status=background_check_status,
            updated_at=datetime.now(UTC),
        )
        self._verification_by_user_id[user_id] = record
        return record


class StubKycProvider(KycProvider):
    async def start_verification(self, user_id: str) -> str:
        nonce = secrets.token_urlsafe(12)
        return f"https://kyc.stub.jobs2go.local/session/{user_id}?nonce={nonce}"


def _hash_password(password: str) -> str:
    # Pilot hash only; Step 13 hardening should replace this with a dedicated password hasher.
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return _hash_password(password) == password_hash


def issue_token() -> str:
    return secrets.token_urlsafe(32)


auth_store: AuthStore = InMemoryAuthStore()
kyc_provider: KycProvider = StubKycProvider()
