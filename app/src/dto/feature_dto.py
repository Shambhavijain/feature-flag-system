from pydantic import BaseModel, Field
from typing import Optional
from enums.enums import Environment


class CreateFeatureDTO(BaseModel):
    name: str
    description: str
    environments: dict[str, bool] = Field(default_factory= dict)

class UpdateFeatureEnvDTO(BaseModel):
    enabled: bool
    rollout_end_at: Optional[str] = None

class EvaluateDTO(BaseModel):
    feature: str
    environment: Environment
    context: dict | None = None
