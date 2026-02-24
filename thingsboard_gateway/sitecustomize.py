"""Runtime compatibility helpers loaded automatically by Python's site module."""

from importlib import metadata
from types import ModuleType
import sys


def _install_pkg_resources_fallback() -> None:
    try:
        __import__("pkg_resources")
        return
    except Exception:
        pass

    module = ModuleType("pkg_resources")

    class DistributionNotFound(Exception):
        """Compatibility exception matching pkg_resources behavior."""

    class Distribution:
        def __init__(self, project_name: str, version: str) -> None:
            self.project_name = project_name
            self.version = version

        def __str__(self) -> str:
            return self.version

    def get_distribution(package_name: str) -> Distribution:
        try:
            version = metadata.version(package_name)
        except metadata.PackageNotFoundError as exc:
            raise DistributionNotFound(package_name) from exc
        return Distribution(package_name, version)

    def parse_version(version: str):
        try:
            from packaging.version import parse as _parse  # Lazy import.

            return _parse(version)
        except Exception:
            return version

    module.DistributionNotFound = DistributionNotFound
    module.get_distribution = get_distribution
    module.parse_version = parse_version
    sys.modules["pkg_resources"] = module


_install_pkg_resources_fallback()
