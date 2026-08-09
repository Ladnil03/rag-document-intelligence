"""Shared enums used across multiple schemas."""

from enum import Enum


class ProcessingStatus(str, Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
