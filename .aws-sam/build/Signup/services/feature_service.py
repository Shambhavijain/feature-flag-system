from datetime import datetime, timezone

from repository.feature_repository import FeatureRepository
from constants.actions import AuditAction
from utils.audit import publish_audit
from utils.utils import map_env_for_audit, map_feature_items, map_audit_items
from dto.feature_dto import (
    CreateFeatureDTO,
    UpdateFeatureEnvDTO,
    EvaluateDTO,
)
from error_handling.exceptions import(
    AppException, 
    EnvironmentNotFoundException,
    FeatureNotFoundException ,
    FeatureAlreadyExistsException
)


class FeatureService:
    def __init__(self, repo: FeatureRepository):
        self.repo = repo

    
    def create_feature(self, request_feature: CreateFeatureDTO, actor: str):
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
                "enviroments":request_feature.environments,
            },
        )

    
    def remove_env(self, feature_name: str, environment: str, actor: str):
        feature_name = feature_name.lower()
        environment = environment.lower()
        existing_env = self.repo.get_env(feature_name, environment)

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

    
    def delete_feature(self, feature_name: str, actor: str):
        feature_name = feature_name.lower()

        existing_items = self.repo.get_feature_items(feature_name)
        if not existing_items:
            raise FeatureNotFoundException(feature_name)

        old =  map_feature_items(existing_items)

        publish_audit(
            feature=feature_name,
            action=AuditAction.DELETE_FEATURE,
            actor=actor,
            old=old,
            new=None,
        )

        self.repo.delete_feature(feature_name)

   
  

    def get_feature(self, feature_name: str):
        feature_name = feature_name.lower()

        items = self.repo.get_feature_items(feature_name)
        if not items:
            raise FeatureNotFoundException(feature_name)

        return map_feature_items(items)

   
    def evaluate(self, request_evaluate: EvaluateDTO) -> bool:
        feature_name = request_evaluate.feature.lower()
        environment = request_evaluate.environment.value.lower()

        feature_items = self.repo.get_feature_items(feature_name)
        if not feature_items:
            raise FeatureNotFoundException(feature_name)

        env_data = self.repo.get_env(feature_name, environment)
        if not env_data:
            raise EnvironmentNotFoundException(feature_name,environment)

        rollout_end = env_data.get("rollout_end_at")
        if rollout_end:
            now = datetime.now(timezone.utc)
            rollout_time = datetime.fromisoformat(
                rollout_end.replace("Z", "")
            ).replace(tzinfo=timezone.utc)

            if now >= rollout_time:
                if not env_data["enabled"]:
                    self.repo.put_env(
                        feature_name=feature_name,
                        env=environment,
                        enabled=True,
                        rollout_end_at=None,
                    )

                    previous_audit = map_env_for_audit(env_data)

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

        return env_data["enabled"]



   
    def get_audit_logs(self, feature_name: str):
        feature_items = self.repo.get_audit_logs(feature_name.lower())
        return map_audit_items(feature_items)

    
    def update_env(
        self,
        feature_name: str,
        environment: str,
        request_feature: UpdateFeatureEnvDTO,
        actor: str,
    ):
        feature_name = feature_name.lower()
        environment = environment.lower()
        raw_existing_env = self.repo.get_env(feature_name, environment)
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
