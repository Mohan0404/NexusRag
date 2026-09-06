"""API request models for NexusRAG (Phase 11).

Defines external HTTP request contracts using Pydantic v2.
"""

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    """Schema for incoming user chat/question requests."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="The user question to be answered using the knowledge base.",
        examples=["What is the annual leave policy?"],
    )

    model_config = {
        "str_strip_whitespace": True,
        "json_schema_extra": {
            "example": {"question": "What is the annual leave policy?"}
        },
    }

    @field_validator("question")
    @classmethod
    def validate_question_not_blank(cls, v: str) -> str:
        """Ensures question is not empty or whitespace-only."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Question must not be empty or whitespace-only.")
        return stripped
