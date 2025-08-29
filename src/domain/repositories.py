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


class PdfDownloader(Protocol):
    def download(self, url: str, case_id: str) -> Any:  # returns Path-like; use Any to avoid circular import
        """Download a PDF returning a filesystem path. Raises RuntimeError on failure."""
        ...
