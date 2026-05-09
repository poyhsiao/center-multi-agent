"""Auth Service - Password hashing and TOTP operations."""
from dataclasses import dataclass
import time

import bcrypt
import pyotp

from app.core.exceptions import InvalidCredentialsException, TOTPRequiredException
from app.services.token_service import TokenService, TokenPair

_TOTP_DIGESTS = {
    "SHA1": "SHA1",
    "SHA256": "SHA256",
    "SHA512": "SHA512",
}


@dataclass
class LoginCredentials:
    """Login request credentials."""
    email: str
    password: str
    device_fingerprint: str
    totp_code: str | None = None


@dataclass
class LoginResult:
    """Login successful result."""
    access_token: str
    refresh_token: str
    expires_in: int


def hash_password(plain_password: str) -> str:
    """
    Hash a plain text password using bcrypt.

    Args:
        plain_password: Plain text password to hash

    Returns:
        bcrypt hash string (60 characters)
    """
    password_bytes = plain_password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a bcrypt hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: bcrypt hash to verify against

    Returns:
        True if password matches, False otherwise
    """
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def generate_totp_secret() -> str:
    """
    Generate a random Base32 secret for TOTP.

    Returns:
        Base32 encoded secret string (at least 20 characters)
    """
    return pyotp.random_base32()


def generate_totp_code(
    secret: str,
    algorithm: str = "SHA1",
    digits: int = 6,
    interval: int = 30,
) -> str:
    """
    Generate a TOTP code at the current time.

    Args:
        secret: Base32 encoded secret key
        algorithm: Hash algorithm (SHA1, SHA256, SHA512)
        digits: Number of digits in the OTP (default 6)
        interval: Time step in seconds (default 30)

    Returns:
        TOTP code as a string of digits
    """
    digest = _TOTP_DIGESTS.get(algorithm.upper(), "SHA1")

    totp = pyotp.TOTP(
        secret,
        digits=digits,
        interval=interval,
        digest=digest,
    )
    return totp.now()


def verify_totp(
    code: str,
    secret: str,
    algorithm: str = "SHA1",
    digits: int = 6,
    interval: int = 30,
    window: int = 1,
) -> bool:
    """
    Verify a TOTP code with ±1 time window tolerance.

    Args:
        code: TOTP code to verify
        secret: Base32 encoded secret key
        algorithm: Hash algorithm (SHA1, SHA256, SHA512)
        digits: Number of digits in the OTP (default 6)
        interval: Time step in seconds (default 30)
        window: Number of time steps to allow before/after current (default 1)

    Returns:
        True if code is valid within window, False otherwise
    """
    digest = _TOTP_DIGESTS.get(algorithm.upper(), "SHA1")

    totp = pyotp.TOTP(
        secret,
        digits=digits,
        interval=interval,
        digest=digest,
    )
    # Check current time and ±window intervals
    current_time = int(time.time())

    for offset in range(-window, window + 1):
        check_time = current_time + (offset * interval)
        if totp.at(check_time) == code:
            return True

    return False


# Placeholder for UserRepository - in production this would be a DB interface
class UserRepository:
    """User repository interface."""

    def find_by_email(self, email: str):
        """Find user by email - to be implemented with DB."""
        raise NotImplementedError


async def authenticate_user_async(
    credentials: LoginCredentials,
    session: "AsyncSession",
) -> LoginResult:
    """
    Authenticate user with email/password and optional TOTP (async version).

    Args:
        credentials: Login credentials including email, password, fingerprint
        session: SQLAlchemy AsyncSession for database access

    Returns:
        LoginResult with access and refresh tokens

    Raises:
        InvalidCredentialsException: If credentials are invalid
        TOTPRequiredException: If TOTP is enabled but code not provided
    """
    from sqlalchemy import select
    from app.models.user import User

    # Find user by email
    stmt = select(User).where(User.email == credentials.email)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise InvalidCredentialsException()

    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        raise InvalidCredentialsException()

    # Check TOTP if enabled
    if user.totp_enabled:
        if not credentials.totp_code:
            raise TOTPRequiredException()

        if not verify_totp(credentials.totp_code, user.totp_secret):
            raise InvalidCredentialsException()

    # Create tokens via TokenService
    token_service = TokenService()
    device_id = "device_" + credentials.device_fingerprint[:8]

    tokens = token_service.create_tokens(
        user_id=str(user.id),
        tenant_id=str(user.org_id),
        device_id=device_id,
        fingerprint=credentials.device_fingerprint,
    )

    return LoginResult(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )


def authenticate_user(credentials: LoginCredentials) -> LoginResult:
    """
    Authenticate user with email/password and optional TOTP.

    Args:
        credentials: Login credentials including email, password, fingerprint

    Returns:
        LoginResult with access and refresh tokens

    Raises:
        InvalidCredentialsException: If credentials are invalid
        TOTPRequiredException: If TOTP is enabled but code not provided
    """
    # Find user by email
    user = UserRepository().find_by_email(credentials.email)

    if user is None:
        raise InvalidCredentialsException()

    # Verify password
    if not verify_password(credentials.password, user.password_hash):
        raise InvalidCredentialsException()

    # Check TOTP if enabled
    if user.totp_enabled:
        if not credentials.totp_code:
            raise TOTPRequiredException()

        if not verify_totp(credentials.totp_code, user.totp_secret):
            raise InvalidCredentialsException()

    # Create tokens via TokenService
    token_service = TokenService()
    device_id = "device_" + credentials.device_fingerprint[:8]

    tokens = token_service.create_tokens(
        user_id=user.id,
        tenant_id=user.tenant_id,
        device_id=device_id,
        fingerprint=credentials.device_fingerprint,
    )

    return LoginResult(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        expires_in=tokens.expires_in,
    )
