from __future__ import annotations

from app.config import load_client_config


def test_load_client_config_smoke():
    cfg, path = load_client_config("partacademy")
    assert cfg.client_name == "partacademy"
    assert path.exists()
