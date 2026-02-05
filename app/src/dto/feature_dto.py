from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime, timezone


from enums.enums import Environment


class CreateFeatureDTO(BaseModel):
    name: str
    description: str
    environments: dict[str, bool] = Field(default_factory= dict)

class UpdateFeatureEnvDTO(BaseModel):
    enabled: bool
    rollout_end_at: Optional[str] = None

    @field_validator("rollout_end_at")
    @classmethod
    def validate_rollout_end_at(cls, value: Optional[str]):
        if value is None:
            return value

        try:
            rollout_time = datetime.fromisoformat(value)
        except ValueError:
            raise ValueError("rollout_end_at must be a valid ISO-8601 datetime string")

        if rollout_time.tzinfo is None:
            rollout_time = rollout_time.replace(tzinfo=timezone.utc)

        if rollout_time <= datetime.now(timezone.utc):
            raise ValueError("rollout_end_at must be a future datetime")

        return value 

class EvaluateDTO(BaseModel):
    feature: str
    environment: Environment
    context: dict | None = None

class FeatureListItemDTO(BaseModel):
    name: str
    description: Optional[str]
    created_at: Optional[str] = None