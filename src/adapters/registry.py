# src/adapters/registry.py
"""
Adapter Registry

Central registry for framework adapters with auto-discovery capabilities.
"""

from typing import Dict, Type, List, Optional
import importlib
import pkgutil

from .base_adapter import FrameworkAdapter


class AdapterRegistry:
    """Central registry for framework adapters"""

    def __init__(self):
        self._adapters: Dict[str, Type[FrameworkAdapter]] = {}

    def register(self, adapter_class: Type[FrameworkAdapter]):
        """Register a framework adapter"""
        # Get framework name from adapter
        temp_instance = adapter_class()
        framework_name = temp_instance.get_framework_name()

        self._adapters[framework_name] = adapter_class

    def get_adapter(self, framework_name: str, config: Optional[Dict] = None) -> FrameworkAdapter:
        """Get adapter instance by framework name"""
        if framework_name not in self._adapters:
            raise ValueError(f"Unknown framework: {framework_name}")

        adapter_class = self._adapters[framework_name]
        return adapter_class(config)

    def has_adapter(self, framework_name: str) -> bool:
        """Check if adapter is registered"""
        return framework_name in self._adapters

    def list_adapters(self) -> List[str]:
        """List all registered adapter names"""
        return list(self._adapters.keys())

    def auto_discover(self):
        """Auto-discover and register all adapters in src/adapters/"""
        import src.adapters

        for _, module_name, _ in pkgutil.iter_modules(src.adapters.__path__):
            if module_name.endswith("_adapter"):
                try:
                    module = importlib.import_module(f"src.adapters.{module_name}")

                    # Find FrameworkAdapter subclasses
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (
                            isinstance(attr, type)
                            and issubclass(attr, FrameworkAdapter)
                            and attr != FrameworkAdapter
                        ):
                            self.register(attr)
                except ImportError:
                    # Skip adapters that can't be imported
                    continue


# Global registry instance
_registry = AdapterRegistry()


def get_registry() -> AdapterRegistry:
    """Get global adapter registry"""
    return _registry
