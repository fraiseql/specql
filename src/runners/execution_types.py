"""Execution type definitions and metadata."""

from dataclasses import dataclass
from enum import Enum


@dataclass
class ExecutionMetadata:
    """Metadata about an execution type."""

    display_name: str
    requires_network: bool
    supports_streaming: bool
    default_timeout: int  # seconds


class ExecutionType(Enum):
    """Supported execution types for job runners."""

    HTTP = ExecutionMetadata(
        display_name="HTTP API",
        requires_network=True,
        supports_streaming=False,
        default_timeout=300,
    )

    SHELL = ExecutionMetadata(
        display_name="Shell Script",
        requires_network=False,
        supports_streaming=True,
        default_timeout=600,
    )

    DOCKER = ExecutionMetadata(
        display_name="Docker Container",
        requires_network=False,
        supports_streaming=True,
        default_timeout=1800,
    )

    SERVERLESS = ExecutionMetadata(
        display_name="Serverless Function",
        requires_network=True,
        supports_streaming=False,
        default_timeout=900,
    )

    @property
    def display_name(self) -> str:
        return self.value.display_name

    @property
    def requires_network(self) -> bool:
        return self.value.requires_network

    @property
    def supports_streaming(self) -> bool:
        return self.value.supports_streaming

    @property
    def default_timeout(self) -> int:
        return self.value.default_timeout
