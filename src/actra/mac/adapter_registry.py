"""Registry for application adapters."""

from __future__ import annotations

import logging
from typing import Any

from actra.mac.app_adapter import AppAdapter

logger = logging.getLogger(__name__)


class AdapterRegistry:
    """Manages registered application adapters and resolves them by name or bundle ID."""

    def __init__(self) -> None:
        self._adapters_by_name: dict[str, AppAdapter] = {}
        self._adapters_by_bundle_id: dict[str, AppAdapter] = {}

    def register(self, adapter: AppAdapter) -> None:
        """Register an AppAdapter instance."""
        name_key = adapter.app_name.lower().strip()
        self._adapters_by_name[name_key] = adapter
        if adapter.bundle_id:
            bundle_key = adapter.bundle_id.lower().strip()
            self._adapters_by_bundle_id[bundle_key] = adapter
        logger.debug("Registered adapter for %s (%s)", adapter.app_name, adapter.bundle_id)

    def get(self, identifier: str) -> AppAdapter | None:
        """Look up an adapter by app name or bundle ID."""
        key = identifier.lower().strip()
        # 1. Direct bundle ID match
        if key in self._adapters_by_bundle_id:
            return self._adapters_by_bundle_id[key]
        # 2. App name match
        if key in self._adapters_by_name:
            return self._adapters_by_name[key]
        return None

    def list_adapters(self) -> list[str]:
        """Return list of registered adapter app names."""
        return [adapter.app_name for adapter in self._adapters_by_name.values()]

    def register_defaults(self) -> None:
        """Register all standard built-in adapters."""
        from actra.mac.adapters.safari_adapter import SafariAdapter
        from actra.mac.adapters.filesystem_adapter import FilesystemAdapter
        from actra.mac.adapters.noop_adapter import NoOpAdapter

        self.register(SafariAdapter())
        self.register(FilesystemAdapter())
        self.register(NoOpAdapter())


# Global default registry singleton
_default_adapter_registry: AdapterRegistry | None = None


def get_adapter_registry() -> AdapterRegistry:
    """Get or initialize the global default adapter registry."""
    global _default_adapter_registry
    if _default_adapter_registry is None:
        _default_adapter_registry = AdapterRegistry()
        _default_adapter_registry.register_defaults()
    return _default_adapter_registry
