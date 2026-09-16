from abc import ABC, abstractmethod
from typing import Any


class AIAdvisorService(ABC):
    """Provider-agnostic interface for the future AI Renewable Energy Advisor.

    Implementations must translate conversation into structured requests for
    the deterministic calculation engines in ``app.engines``, and turn the
    validated engine results back into a plain-language explanation. An
    implementation must never invent system sizes, costs, savings, subsidies,
    or engineering calculations itself — see the architecture note in the
    project README.
    """

    @abstractmethod
    def ask(self, message: str, context: dict[str, Any] | None = None) -> str:
        """Handle a user's natural-language question and return a response."""

    @abstractmethod
    def explain_result(self, result: dict[str, Any]) -> str:
        """Explain a validated calculation engine result in plain language."""

    @abstractmethod
    def request_missing_information(self, missing_fields: list[str]) -> str:
        """Produce a prompt asking the user for the information still required."""

    @abstractmethod
    def execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Invoke a backend tool/function and return its structured result."""
