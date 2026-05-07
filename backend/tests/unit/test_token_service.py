"""Unit tests for Token Service."""
import pytest
from datetime import datetime, timedelta, timezone


class TestJWTOperations:
    """Test JWT signing and verification."""

    def test_jwt_sign_creates_access_token(self):
        """Sign should create a valid JWT access token."""
        from app.core.security import sign_access_token

        token = sign_access_token(
            user_id="user-123",
            tenant_id="tenant-456",
            device_id="device-789",
            fingerprint="fp_abc123",
        )

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_jwt_sign_creates_refresh_token(self):
        """Sign should create a JWT refresh token with jti."""
        from app.core.security import sign_refresh_token

        token = sign_refresh_token(
            user_id="user-123",
            tenant_id="tenant-456",
            device_id="device-789",
            fingerprint="fp_abc123",
        )

        assert token is not None
        assert isinstance(token, str)

    def test_jwt_verify_valid_access_token(self):
        """Verify should return claims for valid access token."""
        from app.core.security import sign_access_token, verify_access_token

        token = sign_access_token(
            user_id="user-123",
            tenant_id="tenant-456",
            device_id="device-789",
            fingerprint="fp_abc123",
        )

        claims = verify_access_token(token)

        assert claims["sub"] == "user-123"
        assert claims["tid"] == "tenant-456"
        assert claims["did"] == "device-789"
        assert claims["fp"] == "fp_abc123"
        assert claims["type"] == "access"

    def test_jwt_verify_valid_refresh_token(self):
        """Verify should return claims including jti for refresh token."""
        from app.core.security import sign_refresh_token, verify_refresh_token

        token = sign_refresh_token(
            user_id="user-123",
            tenant_id="tenant-456",
            device_id="device-789",
            fingerprint="fp_abc123",
        )

        claims = verify_refresh_token(token)

        assert claims["sub"] == "user-123"
        assert claims["jti"] is not None
        assert claims["type"] == "refresh"

    def test_jwt_claims_extraction(self):
        """Should correctly extract all standard claims."""
        from app.core.security import sign_access_token, extract_standard_claims

        token = sign_access_token(
            user_id="user-999",
            tenant_id="tenant-888",
            device_id="device-777",
            fingerprint="fp_xyz",
        )

        claims = extract_standard_claims(token)

        assert claims.user_id == "user-999"
        assert claims.tenant_id == "tenant-888"
        assert claims.device_id == "device-777"
        assert claims.fingerprint == "fp_xyz"

    def test_jwt_expired_token_rejected(self):
        """Expired token should be rejected with TokenExpiredException."""
        from app.core.security import sign_access_token, verify_access_token
        from app.core.exceptions import TokenExpiredException

        # Create a token that's already expired (exp = now - 1 second)
        with pytest.raises(TokenExpiredException):
            verify_access_token("eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyLTEyMyIsImV4cCI6MTYwMDAwMDAwMH0.fake")
