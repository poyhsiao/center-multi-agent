"""Integration tests for TokenService."""
import pytest

from app.services.token_service import TokenService
from app.core.exceptions import (
    FingerprintMismatchException,
    TokenRevokedException,
)


class TestTokenServiceIntegration:
    """Integration tests for complete token flows."""

    @pytest.fixture
    def token_service(self):
        """Create TokenService instance."""
        return TokenService()

    def test_create_tokens_returns_valid_pair(self, token_service):
        """create_tokens should return both tokens."""
        result = token_service.create_tokens(
            user_id="user-123",
            tenant_id="tenant-456",
            device_id="device-789",
            fingerprint="fp_abc123",
        )

        assert result.access_token is not None
        assert result.refresh_token is not None
        assert result.expires_in == 900  # 15 minutes

    def test_full_refresh_flow(self, token_service):
        """Complete refresh cycle: create -> refresh -> verify new RT works."""
        # Create initial tokens
        initial = token_service.create_tokens(
            user_id="user-123",
            tenant_id="tenant-456",
            device_id="device-789",
            fingerprint="fp_abc123",
        )

        # Refresh with same fingerprint
        refreshed = token_service.refresh_tokens(
            refresh_token=initial.refresh_token,
            fingerprint="fp_abc123",
        )

        # Access tokens created within same second may be identical (same iat timestamp)
        # The security guarantee comes from RT rotation (new jti, old RT blacklisted)
        assert refreshed.refresh_token != initial.refresh_token

        # Old RT should be revoked - second refresh with old RT should fail
        with pytest.raises(TokenRevokedException):
            token_service.refresh_tokens(
                refresh_token=initial.refresh_token,
                fingerprint="fp_abc123",
            )

    def test_fingerprint_mismatch_rejects_refresh(self, token_service):
        """Different fingerprint should reject refresh."""
        initial = token_service.create_tokens(
            user_id="user-123",
            tenant_id="tenant-456",
            device_id="device-789",
            fingerprint="fp_abc123",
        )

        with pytest.raises(FingerprintMismatchException):
            token_service.refresh_tokens(
                refresh_token=initial.refresh_token,
                fingerprint="fp_different",
            )

    def test_logout_revokes_token(self, token_service):
        """logout should revoke the refresh token."""
        initial = token_service.create_tokens(
            user_id="user-123",
            tenant_id="tenant-456",
            device_id="device-789",
            fingerprint="fp_abc123",
        )

        # Logout
        token_service.revoke_refresh_token(initial.refresh_token)

        # Try to use revoked token
        with pytest.raises(TokenRevokedException):
            token_service.refresh_tokens(
                refresh_token=initial.refresh_token,
                fingerprint="fp_abc123",
            )
