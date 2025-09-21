import logging
from typing import Dict

from ...domain.log.emit import jlog
from ...domain.port.factory import ViewFactoryRegistry as ViewFactoryRegistryProtocol, ViewFactory
from ...domain.log.code import LogCode

logger = logging.getLogger(__name__)


def _stamp(func: ViewFactory) -> str:
    module = getattr(func, "__module__", "")
    qualname = getattr(func, "__qualname__", getattr(func, "__name__", ""))
    return f"{module}:{qualname}"


def key(factory_func: ViewFactory) -> str:
    return _stamp(factory_func)


class ViewFactoryRegistry(ViewFactoryRegistryProtocol):
    def __init__(self) -> None:
        self._registry: Dict[str, ViewFactory] = {}

    def register(self, name: str, factory: ViewFactory) -> None:
        if name in self._registry:
            jlog(logger, logging.WARNING, LogCode.REGISTRY_REGISTER, key=name, note="duplicate")
            raise KeyError(f"Factory already registered for key: {name}")
        self._registry[name] = factory
        jlog(logger, logging.INFO, LogCode.REGISTRY_REGISTER, key=name, note="ok")

    def enlist(self, factory: ViewFactory) -> str:
        k = _stamp(factory)
        self.register(k, factory)
        return k

    def get(self, key: str) -> ViewFactory:
        try:
            f = self._registry[key]
            jlog(logger, logging.DEBUG, LogCode.REGISTRY_GET, key=key, found=True)
            return f
        except KeyError as e:
            jlog(logger, logging.DEBUG, LogCode.REGISTRY_GET, key=key, found=False)
            raise KeyError(f"Factory not found for key: {key}") from e

    def has(self, key: str) -> bool:
        exists = key in self._registry
        jlog(logger, logging.DEBUG, LogCode.REGISTRY_HAS, key=key, found=exists)
        return exists


default = ViewFactoryRegistry()

__all__ = ["ViewFactoryRegistry", "key", "default"]
