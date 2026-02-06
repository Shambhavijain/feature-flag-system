from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, timezone

from enums.enums import Environment


class CreateFeatureDTO(BaseModel):
    name: str = Field(..., min_length=3, description="Feature name must be at least 3 characters")
    description: str = Field(..., min_length=3, description="Description must be at least 3 characters")
    environments: dict[str, bool] = Field(default_factory=dict)


class UpdateFeatureEnvDTO(BaseModel):
    enabled: bool
    rollout_end_at: Optional[int] = Field(
        None,
        description="Epoch timestamp (seconds), must be in the future"
    )

    @field_validator("rollout_end_at")
    @classmethod
    def validate_rollout_end_at(cls, value: Optional[int]):
        if value is None:
            return value

        if value <= int(datetime.now(timezone.utc).timestamp()):
            raise ValueError("rollout_end_at must be a future epoch timestamp")

        return value



class EvaluateDTO(BaseModel):
    feature: str = Field(..., min_length=3, description="Feature name must be at least 3 characters")
    environment: Environment
    context: dict | None = None


class FeatureListItemDTO(BaseModel):
    name: str = Field(..., min_length=3)
    description: Optional[str] = Field(None, min_length=3)
    created_at: Optional[int] = None
