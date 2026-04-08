"""Base handler result."""

from dataclasses import dataclass
from typing import Optional

@dataclass
class HandlerResult:
    message: str
    success: bool = True

    @staticmethod
    def ok(message: str) -> "HandlerResult":
        return HandlerResult(message=message, success=True)

    @staticmethod
    def fail(error: str, message: str = "") -> "HandlerResult":
        return HandlerResult(message=message or f"Error: {error}", success=False)


@dataclass
class HandlerContext:
    user_id: Optional[int]
    username: Optional[str]
    args: Optional[str]
