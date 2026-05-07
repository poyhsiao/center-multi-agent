"""Custom exceptions for token operations."""


class TokenException(Exception):
    """Base exception for token operations."""

    def __init__(self, message: str, code: str = "token_error"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class TokenExpiredException(TokenException):
    """Token has expired."""

    def __init__(self, message: str = "Token has expired"):
        super().__init__(message, code="token_expired")


class TokenInvalidException(TokenException):
    """Token is invalid."""

    def __init__(self, message: str = "Invalid token"):
        super().__init__(message, code="token_invalid")


class FingerprintMismatchException(TokenException):
    """Device fingerprint does not match."""

    def __init__(self, message: str = "Device fingerprint mismatch"):
        super().__init__(message, code="fingerprint_mismatch")


class TokenRevokedException(TokenException):
    """Token has been revoked."""

    def __init__(self, message: str = "Token has been revoked"):
        super().__init__(message, code="token_revoked")


class InvalidCredentialsException(Exception):
    """Invalid login credentials."""

    def __init__(self, message: str = "Invalid email or password"):
        self.message = message
        self.code = "invalid_credentials"
        super().__init__(self.message)


class TOTPRequiredException(Exception):
    """TOTP verification required but not provided."""

    def __init__(self, message: str = "TOTP code required"):
        self.message = message
        self.code = "totp_required"
        super().__init__(self.message)