"""Abstract AI model interface (placeholder for future ML integration)."""
from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np


class AIModel(ABC):
    @abstractmethod
    def predict(self, features: np.ndarray) -> float: ...

    @abstractmethod
    def train(self, X: np.ndarray, y: np.ndarray) -> None: ...

    @abstractmethod
    def save(self, path: str) -> None: ...

    @abstractmethod
    def load(self, path: str) -> None: ...
