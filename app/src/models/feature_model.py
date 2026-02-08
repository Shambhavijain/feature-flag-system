from dataclasses import dataclass
from typing import Optional, Dict
from enums.enums import Environment


@dataclass(slots=True)
class FeatureMeta:
    name: str
    description: Optional[str]
    created_at: int


@dataclass(slots=True)
class FeatureEnv:
    feature_name: str
    environment: Environment
    enabled: bool
    rollout_end_at: Optional[int]
    updated_at: int


@dataclass(slots=True)
class Feature:
    meta: FeatureMeta
    environments: Dict[Environment, FeatureEnv]


@dataclass(slots=True)
class AuditLog:
    action: str
    actor: str
    old: Optional[dict]
    new: Optional[dict]
    timestamp: int
