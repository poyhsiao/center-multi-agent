"""Integration tests for Redis-based refresh token rotation."""
import pytest
import base64
import json


def extract_jti(token: str) -> str:
    """Extract jti from a JWT refresh token."""
    payload_b64 = token.split(".")[1]
    payload_b64 += "=" * (4 - len(payload_b64) % 4)
    payload = json.loads(base64.b64decode(payload_b64))
    return payload["jti"]


@pytest.mark.asyncio
async def test_rt_rotation_flow(redis_client):
    """Test complete refresh token rotation with sliding window."""
    from app.services.token_service import TokenService
    from app.db.redis import is_token_blacklisted, get_current_jti

    ts = TokenService()
    user_id = "user-rt-test"
    device_id = "device-rt-test"
    fingerprint = "fp_rt_test"

    # Create initial tokens
    result1 = ts.create_tokens(user_id, "tenant-1", device_id, fingerprint)

    original_rt = result1.refresh_token
    original_at = result1.access_token
    original_jti = extract_jti(original_rt)

    # Verify original RT is stored and current
    rt_key = f"rt:{user_id}:{device_id}"
    stored = await redis_client.hgetall(rt_key)
    assert stored["current"] == original_jti

    # Perform rotation via refresh_tokens
    result2 = ts.refresh_tokens(original_rt, fingerprint)

    # Access tokens may be identical if created within same second (same iat)
    # Security guarantee comes from RT rotation (new jti, old RT blacklisted)
    assert result2.refresh_token != original_rt

    # Verify old RT jti is blacklisted
    assert is_token_blacklisted(original_jti) is True

    # Verify new RT jti is now current
    new_jti = extract_jti(result2.refresh_token)
    stored = await redis_client.hgetall(rt_key)
    assert stored["current"] == new_jti


@pytest.mark.asyncio
async def test_fingerprint_mismatch_reject(redis_client):
    """Fingerprint mismatch during refresh should be rejected."""
    from app.services.token_service import TokenService
    from app.core.exceptions import FingerprintMismatchException

    ts = TokenService()
    user_id = "user-fp-test"
    device_id = "device-fp-test"

    result = ts.create_tokens(user_id, "tenant-1", device_id, "fp_original")
    rt = result.refresh_token

    with pytest.raises(FingerprintMismatchException):
        ts.refresh_tokens(rt, "fp_different")


@pytest.mark.asyncio
async def test_blacklist_check(redis_client):
    """Revoked refresh token should be blacklisted."""
    from app.services.token_service import TokenService
    from app.core.exceptions import TokenRevokedException

    ts = TokenService()
    user_id = "user-bl-test"
    device_id = "device-bl-test"

    result = ts.create_tokens(user_id, "tenant-1", device_id, "fp_test")
    ts.revoke_refresh_token(result.refresh_token)

    original_jti = extract_jti(result.refresh_token)

    from app.db.redis import is_token_blacklisted
    assert is_token_blacklisted(original_jti) is True

    with pytest.raises(TokenRevokedException):
        ts.refresh_tokens(result.refresh_token, "fp_test")


@pytest.mark.asyncio
async def test_invalid_jti_during_refresh(redis_client):
    """Refresh with invalid/blacklisted jti should raise TokenRevokedException."""
    from app.services.token_service import TokenService
    from app.core.exceptions import TokenRevokedException
    from app.db.redis import blacklist_refresh_token

    ts = TokenService()
    user_id = "user-invalid-jti"
    device_id = "device-invalid-jti"
    fingerprint = "fp_test"

    # Create a valid token first
    result = ts.create_tokens(user_id, "tenant-1", device_id, fingerprint)

    # Extract jti from the refresh token
    jti = extract_jti(result.refresh_token)

    # Manually blacklist the jti to simulate invalid/expired scenario
    blacklist_refresh_token(jti, ttl_seconds=3600)

    # Try to use the now-blacklisted token - should raise TokenRevokedException
    with pytest.raises(TokenRevokedException):
        ts.refresh_tokens(result.refresh_token, fingerprint)
