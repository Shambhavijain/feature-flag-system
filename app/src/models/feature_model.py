from dataclasses import dataclass
from typing import Optional
from constants.enums import Environment


@dataclass
class FeatureMeta:
    name: str
    description: str
    created_at: str

@dataclass
class FeatureEnv:
    feature_name: str
    environment: Environment
    enabled: bool
    rollout_end_at: Optional[str] 
    updated_at: str
