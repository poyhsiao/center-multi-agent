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


class ResourceNotFoundException(Exception):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        self.message = message
        self.code = "resource_not_found"
        super().__init__(self.message)


class DuplicateResourceException(Exception):
    """Raised when attempting to create a resource that already exists."""

    def __init__(self, message: str = "Resource already exists"):
        self.message = message
        self.code = "duplicate_resource"
        super().__init__(self.message)


class PermissionDeniedException(Exception):
    """Raised when user lacks permission for an action."""

    def __init__(self, message: str = "Permission denied"):
        self.message = message
        self.code = "permission_denied"
        super().__init__(self.message)


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


class ResourceNotFoundException(Exception):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        self.message = message
        self.code = "resource_not_found"
        super().__init__(self.message)


class DuplicateResourceException(Exception):
    """Raised when attempting to create a resource that already exists."""

    def __init__(self, message: str = "Resource already exists"):
        self.message = message
        self.code = "duplicate_resource"
        super().__init__(self.message)


class PermissionDeniedException(Exception):
    """Raised when user lacks permission for an action."""

    def __init__(self, message: str = "Permission denied"):
        self.message = message
        self.code = "permission_denied"
        super().__init__(self.message)
