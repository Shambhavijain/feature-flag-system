from datetime import datetime, timezone

from repository.feature_repository import FeatureRepository
from enums.actions import AuditAction
from utils.audit import publish_audit
from utils.utils import map_env_for_audit, map_audit_items
from models.feature_model import Feature, FeatureEnv, AuditLog
from dto.feature_dto import (
    CreateFeatureDTO,
    UpdateFeatureEnvDTO,
    EvaluateDTO,
    FeatureListItemDTO
)
from error_handling.exceptions import(
    EnvironmentNotFoundException,
    FeatureNotFoundException ,
    FeatureAlreadyExistsException
)


class FeatureService:
    def __init__(self, repo: FeatureRepository):
        self.repo = repo
 
    def create_feature(self, request_feature: CreateFeatureDTO, actor: str)->None:
        feature_name = request_feature.name.lower()

        self.repo.create_feature(
            feature_name,
            request_feature.description,
            request_feature.environments
        )

        publish_audit(
            feature=feature_name,
            action=AuditAction.CREATE_FEATURE,
            actor=actor,
            old=None,
            new={
                "description":request_feature.description,
                "environments":request_feature.environments,
            },
        )
  
    def remove_env(self, feature_name: str, environment: str, actor: str)->None:
        feature_name = feature_name.lower()
        environment = environment.lower()
        existing_env: FeatureEnv | None = self.repo.get_env(feature_name, environment)

        if not existing_env:
            raise EnvironmentNotFoundException(feature_name,environment)

        previous_audit = map_env_for_audit(existing_env)

        self.repo.delete_env(feature_name, environment)

        publish_audit(
            feature=feature_name,
            action=AuditAction.DELETE_ENV,
            actor=actor,
            old=previous_audit,
            new=None,
        )

    def delete_feature(self, feature_name: str, actor: str)->None:
        feature_name = feature_name.lower()

        meta = self.repo.get_feature_details(feature_name)
        if not meta:
            raise FeatureNotFoundException(feature_name)

        envs = self.repo.get_feature_envs(feature_name)

        previous_audit = {
            "feature": meta.name,
            "description": meta.description,
            "created_at": meta.created_at,
            "environments": {
                env.environment.value: {
                    "enabled": env.enabled,
                    "rollout_end_at": env.rollout_end_at,
                    "updated_at": env.updated_at,
                }
                for env in envs
            },
        }

        publish_audit(
            feature=feature_name,
            action=AuditAction.DELETE_FEATURE,
            actor=actor,
            old=previous_audit,
            new=None,
        )

        self.repo.delete_feature(feature_name)



    def get_feature(self, feature_name: str) -> Feature:
        feature_name = feature_name.lower()

        meta = self.repo.get_feature_details(feature_name)
        if not meta:
            raise FeatureNotFoundException(feature_name)

        envs = self.repo.get_feature_envs(feature_name)

        return Feature(
            meta=meta,
            environments={env.environment: env for env in envs},
        )

    def evaluate(self, request_evaluate: EvaluateDTO) -> bool:
        feature_name = request_evaluate.feature.lower()
        environment = request_evaluate.environment.value.lower()

        feature_item = self.repo.get_feature_details(feature_name)
        if not feature_item:
            raise FeatureNotFoundException(feature_name)

        env_data: FeatureEnv | None = self.repo.get_env(feature_name, environment)
        if not env_data:
            raise EnvironmentNotFoundException(feature_name, environment)

        rollout_end = env_data.rollout_end_at
        if rollout_end:
            now = int(datetime.now(timezone.utc).timestamp())

            if now >= rollout_end:
                if not env_data.enabled:
                    previous_audit = map_env_for_audit(env_data)
                    self.repo.put_env(
                        feature_name=feature_name,
                        env=environment,
                        enabled=True,
                        rollout_end_at=None,
                    )

                    publish_audit(
                        feature=feature_name,
                        action=AuditAction.AUTO_ROLLOUT,
                        actor="SYSTEM",
                        old=previous_audit,
                        new={
                            "environment": environment,
                            "enabled": True,
                        },
                    )
                return True

        return env_data.enabled


    def get_audit_logs(self, feature_name: str)-> list[AuditLog]:
        feature_items = self.repo.get_audit_logs(feature_name.lower())
        return map_audit_items(feature_items)
  
    def update_env(
        self,
        feature_name: str,
        environment: str,
        request_feature: UpdateFeatureEnvDTO,
        actor: str,
    )->None:
        feature_name = feature_name.lower()
        environment = environment.lower()
        raw_existing_env: FeatureEnv | None = self.repo.get_env(feature_name, environment)
        if not raw_existing_env:
            raise EnvironmentNotFoundException(feature_name,environment)

        previous_audit = map_env_for_audit(raw_existing_env)

        self.repo.put_env(
            feature_name=feature_name,
            env=environment,
            enabled=request_feature.enabled,
            rollout_end_at=request_feature.rollout_end_at,
        )

        current_audit = {
            "environment": environment,
            **request_feature.model_dump(),
        }

        publish_audit(
            feature=feature_name,
            action=AuditAction.UPDATE_ENV,
            actor=actor,
            old=previous_audit,
            new=current_audit,
        )

    def list_features(self)-> list[FeatureListItemDTO]:
        features = self.repo.get_features()

        return [
            FeatureListItemDTO(
                name=feature.name,
                description=feature.description,
                created_at=feature.created_at,
            )
            for feature in features
        ]


