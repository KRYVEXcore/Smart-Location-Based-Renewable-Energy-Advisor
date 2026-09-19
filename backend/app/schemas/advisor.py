import uuid
from typing import Literal

from pydantic import BaseModel, Field, field_validator

MAX_MESSAGE_CHARS = 1000
MAX_HISTORY_TURN_CHARS = 2000
MAX_HISTORY_TURNS = 20  # request-size ceiling only; the service sends the last few

# ok: a real answer. ai_not_configured: no provider/key on the server.
# ai_error: the provider failed; error_code says how, without provider detail.
AdvisorStatus = Literal["ok", "ai_not_configured", "ai_error"]


class ChatTurn(BaseModel):
    """A prior turn. Roles are limited so a caller cannot inject a "system" turn."""

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=MAX_HISTORY_TURN_CHARS)


class AdvisorChatRequest(BaseModel):
    assessment_id: uuid.UUID
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)
    history: list[ChatTurn] = Field(default_factory=list, max_length=MAX_HISTORY_TURNS)

    @field_validator("message", mode="before")
    @classmethod
    def _strip(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class AdvisorChatResponse(BaseModel):
    status: AdvisorStatus
    message: str | None = None
    error_code: str | None = None
    assessment_id: uuid.UUID
    provider: str | None = None
    model: str | None = None


class AdvisorOverviewResponse(BaseModel):
    """What the chat panel may show before any AI call. No AI request is made for this."""

    assessment_id: uuid.UUID
    ai_configured: bool
    location_label: str | None = None
    building_type: str
    monthly_consumption_kwh: float | None = None
    available: dict[str, bool]
    suggested_questions: list[str]
