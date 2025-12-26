"""
Tests for config loading.
"""
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from app.config import load_client_config, ClientConfig


def test_load_client_config(tmp_path, monkeypatch):
    """Test loading a valid client config."""
    client_name = "test_client"
    config_dir = tmp_path / "clients" / client_name
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config.yaml"
    
    config_data = {
        "site": {
            "name": "test.com",
            "timezone": "Europe/Moscow",
        },
        "metrika": {
            "counter_id": 12345678,
            "goal_id": 123456,
            "currency": "RUB",
        },
    }
    
    config_file.write_text(yaml.dump(config_data), encoding="utf-8")
    
    # Mock clients directory by patching the function
    from app import config
    original_clients_dir = config.CLIENTS_DIR
    config.CLIENTS_DIR = tmp_path / "clients"
    
    try:
        cfg, cfg_path = load_client_config(client_name)
        
        assert cfg.site_name == "test.com"
        assert cfg.counter_id == 12345678
        assert cfg_path == config_file
    finally:
        config.CLIENTS_DIR = original_clients_dir


def test_load_client_config_missing_file():
    """Test loading a non-existent client config."""
    with pytest.raises(FileNotFoundError):
        load_client_config("nonexistent_client")


def test_client_config_defaults():
    """Test ClientConfig with default values."""
    cfg = ClientConfig(
        site_name="test.com",
        timezone="Europe/Moscow",
        counter_id=12345678,
        goal_id=0,
        currency="RUB",
        gsc_site_url="",
        ym_webmaster_user_id="",
        ym_webmaster_host_id="",
    )
    
    assert cfg.site_name == "test.com"
    assert cfg.counter_id == 12345678
    assert cfg.goal_id == 0

