"""Router for Jobs2Go auth and KYC interfaces."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.gateway.routers.jobs2go_auth_service import auth_store, issue_token, kyc_provider, verify_password
from app.gateway.routers.jobs2go_common import Jobs2GoModuleStatus

router = APIRouter(prefix="/v1", tags=["jobs2go-auth"])


class RegisterRequest(BaseModel):
    role: str = Field(pattern="^(employer|worker|both)$")
    email: str
    phone: str | None = None
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthUserResponse(BaseModel):
    id: str
    role: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: AuthUserResponse


class KycStartResponse(BaseModel):
    verification_url: str


class VerificationStatus(BaseModel):
    kyc_status: str
    background_check_status: str


@router.get("/auth/_status", response_model=Jobs2GoModuleStatus)
async def auth_status() -> Jobs2GoModuleStatus:
    """Status endpoint for auth module readiness."""
    return Jobs2GoModuleStatus(
        module="auth",
        status="active",
        next_step="Wire persistent user store in Step 13 hardening",
    )


@router.post("/auth/register", response_model=AuthResponse, status_code=201)
async def register_user(payload: RegisterRequest) -> AuthResponse:
    """Register a new Jobs2Go user for pilot flows."""
    try:
        user = await auth_store.create_user(
            role=payload.role,
            email=payload.email,
            phone=payload.phone,
            password=payload.password,
        )
    except ValueError as exc:
        if str(exc) == "email_already_exists":
            raise HTTPException(status_code=409, detail="User already exists") from exc
        raise

    return AuthResponse(
        access_token=issue_token(),
        refresh_token=issue_token(),
        user=AuthUserResponse(id=user.id, role=user.role),
    )


@router.post("/auth/login", response_model=AuthResponse)
async def login_user(payload: LoginRequest) -> AuthResponse:
    """Authenticate an existing Jobs2Go user for pilot flows."""
    user = await auth_store.get_user_by_email(payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return AuthResponse(
        access_token=issue_token(),
        refresh_token=issue_token(),
        user=AuthUserResponse(id=user.id, role=user.role),
    )


@router.post("/kyc/start", response_model=KycStartResponse)
async def start_kyc(user_id: str = Query(..., description="User ID to start KYC for")) -> KycStartResponse:
    """Start KYC verification session with provider abstraction."""
    user = await auth_store.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    verification_url = await kyc_provider.start_verification(user_id)
    await auth_store.set_verification(
        user_id=user_id,
        kyc_status="pending",
        background_check_status="not_requested",
    )
    return KycStartResponse(verification_url=verification_url)


@router.get("/users/{userId}/verification", response_model=VerificationStatus)
async def get_verification_status(userId: str) -> VerificationStatus:
    """Return KYC and background verification status for a user."""
    user = await auth_store.get_user_by_id(userId)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    verification = await auth_store.get_verification(userId)
    if verification is None:
        return VerificationStatus(kyc_status="unverified", background_check_status="not_requested")

    return VerificationStatus(
        kyc_status=verification.kyc_status,
        background_check_status=verification.background_check_status,
    )


@router.get("/kyc/_status", response_model=Jobs2GoModuleStatus)
async def kyc_status() -> Jobs2GoModuleStatus:
    """Status endpoint for KYC module readiness."""
    return Jobs2GoModuleStatus(
        module="kyc",
        status="active",
        next_step="Connect provider callback webhook in Step 13 hardening",
    )
