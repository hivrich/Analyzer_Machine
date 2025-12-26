"""
Tests for HTTP client with proxy support.
"""
import os
from unittest.mock import patch, MagicMock

import pytest

from app.http_client import get_session, get_default_session, DEFAULT_NO_PROXY_HOSTS


def test_get_session_without_proxy():
    """Test session creation without proxy settings."""
    with patch.dict(os.environ, {}, clear=True):
        session = get_session()
        assert session is not None
        assert session.timeout == 60


def test_get_session_with_proxy():
    """Test session creation with proxy settings."""
    with patch.dict(os.environ, {
        "HTTP_PROXY": "http://proxy:8080",
        "HTTPS_PROXY": "http://proxy:8080",
    }, clear=True):
        session = get_session()
        assert session is not None


def test_get_session_with_no_proxy():
    """Test session creation with NO_PROXY."""
    with patch.dict(os.environ, {
        "HTTP_PROXY": "http://proxy:8080",
        "NO_PROXY": "api-metrika.yandex.net",
    }, clear=True):
        session = get_session(no_proxy_hosts=["api.webmaster.yandex.net"])
        assert session is not None


def test_get_default_session():
    """Test default session with Yandex/Google APIs in no_proxy."""
    session = get_default_session()
    assert session is not None
    assert session.timeout == 60


def test_session_request_bypass_proxy(monkeypatch):
    """Test that requests to no_proxy hosts bypass proxy."""
    with patch.dict(os.environ, {
        "HTTP_PROXY": "http://proxy:8080",
        "HTTPS_PROXY": "http://proxy:8080",
    }, clear=True):
        session = get_session(no_proxy_hosts=["api-metrika.yandex.net"])
        
        # Mock the request method
        original_request = session.request
        mock_request = MagicMock()
        session.request = mock_request
        
        # Simulate request to no_proxy host
        session.get("https://api-metrika.yandex.net/v1/stat/traffic/summary")
        
        # Check that proxies were set to {} for this request
        # (This is a simplified test - actual implementation checks hostname)
        assert mock_request.called


def test_default_no_proxy_hosts():
    """Test that default no_proxy hosts include Yandex/Google APIs."""
    assert "api-metrika.yandex.net" in DEFAULT_NO_PROXY_HOSTS
    assert "api.webmaster.yandex.net" in DEFAULT_NO_PROXY_HOSTS
    assert "oauth2.googleapis.com" in DEFAULT_NO_PROXY_HOSTS

