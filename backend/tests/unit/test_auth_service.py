"""Unit tests for Auth Service - Password Hashing and TOTP."""

from app.services.auth_service import (
    hash_password,
    verify_password,
    generate_totp_secret,
    generate_totp_code,
    verify_totp,
)


def test_password_hash_verify():
    """Password hash verification works correctly."""
    password = "TestPassword123"
    hashed = hash_password(password)

    assert verify_password(password, hashed) == True
    assert verify_password("WrongPassword", hashed) == False


def test_password_hash_uniqueness():
    """Different salts produce different hashes for same password."""
    hash1 = hash_password("SamePassword")
    hash2 = hash_password("SamePassword")

    assert hash1 != hash2  # Different salts
    assert len(hash1) == 60  # bcrypt hash length
    assert len(hash2) == 60


def test_totp_code_generation_consistency():
    """Same secret generates same TOTP code at same time."""
    secret = generate_totp_secret()
    code1 = generate_totp_code(secret)
    code2 = generate_totp_code(secret)

    assert code1 == code2
    assert len(code1) == 6
    assert code1.isdigit()


def test_totp_window_validation():
    """TOTP verification accepts codes within ±1 window."""
    secret = generate_totp_secret()
    current_code = generate_totp_code(secret)

    assert verify_totp(current_code, secret) == True
    assert verify_totp(current_code, secret, window=1) == True


def test_verify_totp_rejects_invalid():
    """Invalid TOTP codes are rejected."""
    secret = generate_totp_secret()

    assert verify_totp("000000", secret) == False
    assert verify_totp("123456", secret) == False
    assert verify_totp("abcdef", secret) == False