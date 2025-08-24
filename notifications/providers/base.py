# notifications/providers/base.py
from dataclasses import dataclass

@dataclass
class ProviderResult:
    message_id: str
    delivered: bool = False
    raw: dict | None = None

class BaseProvider:
    def send(self, to: str, message: str, **kwargs) -> ProviderResult: ...
