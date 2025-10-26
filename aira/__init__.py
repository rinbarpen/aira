"""Aira 持续对话机器人的核心包。"""

from importlib import metadata


def get_version() -> str:
    """Return installed package version."""

    try:
        return metadata.version("aira")
    except metadata.PackageNotFoundError:  # pragma: no cover
        return "0.0.0"


__all__ = ["get_version"]

