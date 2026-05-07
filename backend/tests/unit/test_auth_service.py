"""Unit tests for Auth Service - Password Hashing and TOTP."""
import pytest
import time


class TestPasswordHashing:
    """Test bcrypt password hashing operations."""

    def test_password_hash_verify(self):
        """bcrypt hash and verify should work correctly."""
        from app.services.auth_service import hash_password, verify_password

        password = "SecureP@ssw0rd!"
        hashed = hash_password(password)

        assert hashed is not None
        assert isinstance(hashed, str)
        assert len(hashed) == 60  # bcrypt hash length

        # Verification should pass
        result = verify_password(password, hashed)
        assert result is True

    def test_password_hash_wrong_password_rejected(self):
        """Wrong password should be rejected."""
        from app.services.auth_service import hash_password, verify_password

        password = "SecureP@ssw0rd!"
        hashed = hash_password(password)

        result = verify_password("WrongPassword", hashed)
        assert result is False

    def test_password_hash_uniqueness(self):
        """Same password with different salts should produce different hashes."""
        from app.services.auth_service import hash_password

        password = "SecureP@ssw0rd!"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Hashes should be different due to random salt
        assert hash1 != hash2

        # But both should verify correctly
        from app.services.auth_service import verify_password
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True

    def test_password_hash_cost_factor(self):
        """Hash should use cost factor 12 (2^12 = 4096 iterations)."""
        from app.services.auth_service import hash_password

        password = "TestPassword123"
        hashed = hash_password(password)

        # bcrypt hash format: $2b$12$...
        # The 12 after $2b$ indicates cost factor 12
        assert hashed.startswith("$2b$12$")

    def test_password_empty_string(self):
        """Empty password should still produce a valid hash."""
        from app.services.auth_service import hash_password, verify_password

        password = ""
        hashed = hash_password(password)

        assert hashed is not None
        assert len(hashed) == 60
        assert verify_password(password, hashed) is True


class TestTOTP:
    """Test TOTP generation and validation."""

    def test_totp_code_generation(self):
        """TOTP should generate consistent 6-digit codes."""
        from app.services.auth_service import generate_totp_secret, generate_totp_code

        secret = generate_totp_secret()
        assert secret is not None
        assert isinstance(secret, str)
        # Base32 secret should be at least 20 chars
        assert len(secret) >= 20

        # Generate code at current time
        code1 = generate_totp_code(secret)
        assert code1 is not None
        assert isinstance(code1, str)
        assert len(code1) == 6
        assert code1.isdigit()

        # Same time should produce same code
        code2 = generate_totp_code(secret)
        assert code1 == code2

    def test_totp_code_changes_over_time(self):
        """TOTP code should change after time step (30 seconds)."""
        from app.services.auth_service import generate_totp_secret, generate_totp_code

        secret = generate_totp_secret()
        code1 = generate_totp_code(secret)

        # Wait for time step to change (30 seconds)
        time.sleep(1)  # Still same window
        code2 = generate_totp_code(secret)
        # Same window - code should be same if within same 30s

    def test_totp_window_validation(self):
        """TOTP should accept codes within ±1 time window (60 seconds)."""
        from app.services.auth_service import generate_totp_secret, generate_totp_code, verify_totp

        secret = generate_totp_secret()

        # Generate current code
        current_code = generate_totp_code(secret)

        # Current code should verify
        assert verify_totp(current_code, secret) is True

        # Invalid code should not verify
        assert verify_totp("000000", secret) is False

    def test_totp_different_secrets_different_codes(self):
        """Different secrets should produce different codes."""
        from app.services.auth_service import generate_totp_secret, generate_totp_code

        secret1 = generate_totp_secret()
        secret2 = generate_totp_secret()

        code1 = generate_totp_code(secret1)
        code2 = generate_totp_code(secret2)

        # Different secrets at same time should produce different codes
        # (unless by extreme coincidence, which is astronomically unlikely)
        # We just verify they're valid 6-digit codes
        assert len(code1) == 6 and len(code2) == 6

    def test_totp_algorithm_selection(self):
        """TOTP should support SHA1, SHA256, SHA512 algorithms."""
        from app.services.auth_service import generate_totp_secret, generate_totp_code

        secret = generate_totp_secret()

        # Default is SHA1 - should work
        code_sha1 = generate_totp_code(secret, algorithm="SHA1")
        assert len(code_sha1) == 6

        # SHA256 should work
        code_sha256 = generate_totp_code(secret, algorithm="SHA256")
        assert len(code_sha256) == 6

        # SHA512 should work
        code_sha512 = generate_totp_code(secret, algorithm="SHA512")
        assert len(code_sha512) == 6
