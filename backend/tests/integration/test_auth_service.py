"""Integration tests for Auth Service - Login Flow."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestLoginFlow:
    """Test login flow integration with Token Service."""

    @pytest.fixture
    def mock_user_repo(self):
        """Create a mock user repository."""
        mock = MagicMock()
        return mock

    @pytest.fixture
    def mock_token_service(self):
        """Create a mock token service."""
        mock = MagicMock()
        mock.create_tokens.return_value = MagicMock(
            access_token="mock_access_token",
            refresh_token="mock_refresh_token",
            expires_in=900,
        )
        return mock

    def test_login_success_flow(self, mock_user_repo, mock_token_service):
        """Successful login should return tokens."""
        from app.services.auth_service import LoginCredentials
        from app.services.auth_service import authenticate_user

        # Mock user with hashed password
        mock_password = "SecureP@ssw0rd!"
        from app.services.auth_service import hash_password
        hashed = hash_password(mock_password)

        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.tenant_id = "tenant-456"
        mock_user.password_hash = hashed
        mock_user.totp_enabled = False

        mock_user_repo.find_by_email.return_value = mock_user

        # Create login credentials
        credentials = LoginCredentials(
            email="test@example.com",
            password=mock_password,
            device_fingerprint="fp_abc123",
        )

        # Authenticate
        with patch("app.services.auth_service.UserRepository", return_value=mock_user_repo):
            with patch("app.services.auth_service.TokenService", return_value=mock_token_service):
                result = authenticate_user(credentials)

        assert result is not None
        assert result.access_token == "mock_access_token"
        assert result.refresh_token == "mock_refresh_token"
        assert result.expires_in == 900

    def test_login_wrong_password_rejected(self, mock_user_repo):
        """Wrong password should be rejected."""
        from app.services.auth_service import LoginCredentials
        from app.services.auth_service import authenticate_user
        from app.core.exceptions import InvalidCredentialsException

        mock_password = "SecureP@ssw0rd!"
        from app.services.auth_service import hash_password
        hashed = hash_password(mock_password)

        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.tenant_id = "tenant-456"
        mock_user.password_hash = hashed
        mock_user.totp_enabled = False

        mock_user_repo.find_by_email.return_value = mock_user

        credentials = LoginCredentials(
            email="test@example.com",
            password="WrongPassword",
            device_fingerprint="fp_abc123",
        )

        with patch("app.services.auth_service.UserRepository", return_value=mock_user_repo):
            with pytest.raises(InvalidCredentialsException):
                authenticate_user(credentials)

    def test_login_totp_required(self, mock_user_repo, mock_token_service):
        """User with TOTP enabled should require TOTP verification."""
        from app.services.auth_service import LoginCredentials
        from app.services.auth_service import authenticate_user
        from app.core.exceptions import TOTPRequiredException

        mock_password = "SecureP@ssw0rd!"
        from app.services.auth_service import hash_password
        hashed = hash_password(mock_password)

        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.tenant_id = "tenant-456"
        mock_user.password_hash = hashed
        mock_user.totp_enabled = True
        mock_user.totp_secret = "JBSWY3DPEHPK3PXP"

        mock_user_repo.find_by_email.return_value = mock_user

        credentials = LoginCredentials(
            email="test@example.com",
            password=mock_password,
            device_fingerprint="fp_abc123",
        )

        with patch("app.services.auth_service.UserRepository", return_value=mock_user_repo):
            with pytest.raises(TOTPRequiredException):
                authenticate_user(credentials)

    def test_login_totp_invalid_rejected(self, mock_user_repo, mock_token_service):
        """Invalid TOTP code should be rejected."""
        from app.services.auth_service import LoginCredentials
        from app.services.auth_service import authenticate_user
        from app.core.exceptions import InvalidCredentialsException

        mock_password = "SecureP@ssw0rd!"
        from app.services.auth_service import hash_password
        hashed = hash_password(mock_password)

        mock_user = MagicMock()
        mock_user.id = "user-123"
        mock_user.tenant_id = "tenant-456"
        mock_user.password_hash = hashed
        mock_user.totp_enabled = True
        mock_user.totp_secret = "JBSWY3DPEHPK3PXP"

        mock_user_repo.find_by_email.return_value = mock_user

        credentials = LoginCredentials(
            email="test@example.com",
            password=mock_password,
            device_fingerprint="fp_abc123",
            totp_code="000000",  # Invalid code
        )

        with patch("app.services.auth_service.UserRepository", return_value=mock_user_repo):
            with pytest.raises(InvalidCredentialsException):
                authenticate_user(credentials)

    def test_login_user_not_found(self, mock_user_repo):
        """Non-existent user should raise exception."""
        from app.services.auth_service import LoginCredentials
        from app.services.auth_service import authenticate_user
        from app.core.exceptions import InvalidCredentialsException

        mock_user_repo.find_by_email.return_value = None

        credentials = LoginCredentials(
            email="nonexistent@example.com",
            password="anypassword",
            device_fingerprint="fp_abc123",
        )

        with patch("app.services.auth_service.UserRepository", return_value=mock_user_repo):
            with pytest.raises(InvalidCredentialsException):
                authenticate_user(credentials)
