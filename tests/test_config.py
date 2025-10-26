from __future__ import annotations

from pathlib import Path

import pytest

from aira.core.config import ConfigLoader, get_mcp_config


def test_config_loader_reads_app_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    app_config = config_dir / "aira.toml"
    app_config.write_text("[app]\nname='aira-test'\n")

    loader = ConfigLoader(base_dir=tmp_path)
    data = loader.load("config/aira.toml")

    assert data["app"]["name"] == "aira-test"


def test_get_mcp_config_from_json(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    json_file = config_dir / "mcp_servers.json"
    json_file.write_text(
        """
        {
          "servers": [{"id": "s1", "url": "http://loc"}],
          "groups": [{"id": "g1", "enabled": true, "servers": ["s1"]}]
        }
        """
    )

    loader = ConfigLoader(base_dir=tmp_path)
    config_loader._cache.clear()  # type: ignore[attr-defined]
    cfg = get_mcp_config()
    assert cfg["servers"][0]["id"] == "s1"

