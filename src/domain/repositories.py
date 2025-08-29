from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Protocol, Any


class StorageRepository(ABC):
    @abstractmethod
    def save(self, key: str, data: bytes) -> None: 
        ...

    @abstractmethod
    def load(self, key: str) -> bytes:  
        ...


class ILlmClient(Protocol):
    async def generate(self, prompt: str, **kwargs: Any) -> str: 
        ...
