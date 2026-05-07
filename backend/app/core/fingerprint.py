"""Device fingerprint generation."""
import hashlib

from app.config import settings


def generate_fingerprint(
    user_agent: str,
    client_version: str,
    client_type: str,
    salt: str | None = None,
) -> str:
    """
    Generate a device fingerprint from components.

    Format: SHA256(agent_hash + client_version + client_type + salt)

    Args:
        user_agent: Browser or client user agent string
        client_version: Application version (e.g., "1.0.0")
        client_type: Client type ("web", "desktop", "mobile")
        salt: Optional salt override (uses config salt by default)

    Returns:
        SHA256 hex digest of combined components
    """
    if salt is None:
        salt = settings.fingerprint_salt

    # Hash the user agent for privacy
    agent_hash = hashlib.sha256(user_agent.encode()).hexdigest()[:16]

    # Combine all components
    raw = f"{agent_hash}{client_version}{client_type}{salt}"

    # Final fingerprint
    return hashlib.sha256(raw.encode()).hexdigest()