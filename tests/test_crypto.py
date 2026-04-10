"""Tests for envault.crypto encryption/decryption module."""

import pytest
from envault.crypto import encrypt, decrypt


PASSWORD = "super-secret-passphrase"
PLAINTEXT = "DATABASE_URL=postgres://user:pass@localhost/db"


def test_encrypt_returns_string():
    token = encrypt(PLAINTEXT, PASSWORD)
    assert isinstance(token, str)
    assert len(token) > 0


def test_encrypt_decrypt_roundtrip():
    token = encrypt(PLAINTEXT, PASSWORD)
    result = decrypt(token, PASSWORD)
    assert result == PLAINTEXT


def test_encrypt_produces_unique_tokens():
    """Each encryption call should produce a different token due to random salt/nonce."""
    token1 = encrypt(PLAINTEXT, PASSWORD)
    token2 = encrypt(PLAINTEXT, PASSWORD)
    assert token1 != token2


def test_decrypt_wrong_password_raises():
    token = encrypt(PLAINTEXT, PASSWORD)
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt(token, "wrong-password")


def test_decrypt_corrupted_token_raises():
    token = encrypt(PLAINTEXT, PASSWORD)
    corrupted = token[:-4] + "AAAA"
    with pytest.raises(ValueError):
        decrypt(corrupted, PASSWORD)


def test_decrypt_invalid_base64_raises():
    with pytest.raises(ValueError, match="Invalid token format|Decryption failed|too short"):
        decrypt("not-valid-base64!!!", PASSWORD)


def test_decrypt_too_short_token_raises():
    import base64
    short_token = base64.urlsafe_b64encode(b"short").decode()
    with pytest.raises(ValueError, match="too short"):
        decrypt(short_token, PASSWORD)


def test_encrypt_empty_string():
    token = encrypt("", PASSWORD)
    result = decrypt(token, PASSWORD)
    assert result == ""


def test_encrypt_unicode_plaintext():
    unicode_text = "SECRET=caf\u00e9-\u4e2d\u6587-\u00e9l\u00e8ve"
    token = encrypt(unicode_text, PASSWORD)
    result = decrypt(token, PASSWORD)
    assert result == unicode_text
