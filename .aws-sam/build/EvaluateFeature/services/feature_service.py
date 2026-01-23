# from datetime import datetime, timezone

# from repository.feature_repository import FeatureRepository
# from constants.actions import AuditAction
# from utils.audit import publish_audit
# from utils.utils import map_env_for_audit
# from dto.feature_dto import (
#     CreateFeatureDTO,
#     UpdateFeatureEnvDTO,
#     EvaluateDTO,
# )


# class FeatureService:
#     def __init__(self, repo: FeatureRepository):
#         self.repo = repo

#     def create_feature(self, request_feature: CreateFeatureDTO, actor: str):
#         self.repo.create_feature(request_feature.name, request_feature.description)

#         feature_name= feature_name.lower()
        
#         publish_audit(
#             feature=request_feature.name,
#             action=AuditAction.CREATE_FEATURE,
#             actor=actor,
#             old=None,
#             new=request_feature.model_dump(),
#         )

    
#     def remove_env(self, feature_name: str, env: str, actor: str):
#         existing_env = self.repo.get_env(feature_name, env)
#         if not existing_env:
#             raise AppException("Environment not found", 404)

#         self.repo.delete_env(feature_name, env)
#         feature_name= feature_name.lower()
#         previous_audit = map_env_for_audit(existing_env)
#         publish_audit(
#             feature=feature_name,
#             action=AuditAction.DELETE_ENV,
#             actor=actor,
#             old=previous_audit,
#             new=None,
#     )


#     def delete_feature(self, feature_name: str, actor: str):
#         existing_feature = self.repo.get_feature(feature_name)
#         old = {
#             "feature": feature_name,
#             "description": existing_feature.get("description"),
#         }
#         feature_name= feature_name.lower()
#         publish_audit(
#             feature=feature_name,
#             action=AuditAction.DELETE_FEATURE,
#             actor=actor,
#             old=old,
#             new=None,
#         )

#         self.repo.delete_feature(feature_name)

       
#     def get_feature(self, flag:str):
#         return self.repo.get_feature(flag)
    
#     def evaluate(self, request_evaluate: EvaluateDTO) -> bool:
#         env_data = self.repo.get_env(request_evaluate.feature, request_evaluate.environment.value)

#         if not env_data:
#             return False

#         rollout_end = env_data.get("rollout_end_at")

#         if rollout_end:
#             now = datetime.now(timezone.utc)
#             rollout_time = datetime.fromisoformat(
#                 rollout_end.replace("Z", "")
#             )

#             if now >= rollout_time:
#                 if not env_data["enabled"]:
#                     self.repo.put_env(
#                         feature_name=request_evaluate.feature,
#                         env=request_evaluate.environment.value,
#                         enabled=True,
#                         rollout_end_at=None,
#                     )
#                     existing_audit = map_env_for_audit(env_data)

#                     publish_audit(
#                         feature=request_evaluate.feature,
#                         action=AuditAction.AUTO_ROLLOUT,
#                         actor="SYSTEM",
#                         old=existing_audit,
#                         new={
#                             "environment": request_evaluate.environment.value,
#                             "enabled": True,
#                         },
#                     )
#                 return True

#         return env_data["enabled"]

#     def get_audit_logs(self, flag: str):
#         return self.repo.get_audit_logs(flag)

#     def update_env(
#         self,
#         feature_name: str,
#         env: str,
#         request_feature: UpdateFeatureEnvDTO,
#         actor: str,):
#         raw_existing_env = self.repo.get_env(feature_name, env)
#         if not raw_existing_env:
#             raise AppException("Environment not found", 404)

#         old = map_env_for_audit(raw_existing_env)
#         feature_name= feature_name.lower()

#         self.repo.put_env(
#             feature_name=feature_name,
#             env=env,
#             enabled=request_feature.enabled,
#             rollout_end_at=request_feature.rollout_end_at,
#         )

#         new = {
#             "environment": env,
#             **request_feature.model_dump(),
#         }

#         publish_audit(
#             feature=feature_name,
#             action=AuditAction.UPDATE_ENV,
#             actor=actor,
#             old=old,
#             new=new,
#         )
    
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
from error_handling.exceptions import AppException


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
            new=request_feature.model_dump(),
        )

    
    def remove_env(self, feature_name: str, env: str, actor: str):
        feature_name = feature_name.lower()

        existing_env = self.repo.get_env(feature_name, env)
        if not existing_env:
            raise AppException("Environment not found", 404)

        previous_audit = map_env_for_audit(existing_env)

        self.repo.delete_env(feature_name, env)

        publish_audit(
            feature=feature_name,
            action=AuditAction.DELETE_ENV,
            actor=actor,
            old=previous_audit,
            new=None,
        )

    
    def delete_feature(self, feature_name: str, actor: str):
        feature_name = feature_name.lower()

        existing_items = self.repo.get_feature(feature_name)
        if not existing_items:
            raise AppException("Feature not found", 404)

        old = {
            "feature": feature_name,
        }

        publish_audit(
            feature=feature_name,
            action=AuditAction.DELETE_FEATURE,
            actor=actor,
            old=old,
            new=None,
        )

        self.repo.delete_feature(feature_name)

   
  

    def get_feature(self, flag: str):
        flag = flag.lower()

        items = self.repo.get_feature(flag)
        if not items:
            raise AppException("Feature not found", 404)

        return map_feature_items(items)

   
    def evaluate(self, request_evaluate: EvaluateDTO) -> bool:
        feature_name = request_evaluate.feature.lower()
        env = request_evaluate.environment.value

        items = self.repo.get_feature(feature_name)
        if not items:
            raise AppException("Feature not found", 404)

        env_data = self.repo.get_env(feature_name, env)
        if not env_data:
            raise AppException(
                f"Feature not found in environment {env}",
                404
            )

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
                        env=env,
                        enabled=True,
                        rollout_end_at=None,
                    )

                    old = map_env_for_audit(env_data)

                    publish_audit(
                        feature=feature_name,
                        action=AuditAction.AUTO_ROLLOUT,
                        actor="SYSTEM",
                        old=old,
                        new={
                            "environment": env,
                            "enabled": True,
                        },
                    )
                return True

        return env_data["enabled"]



   
    def get_audit_logs(self, flag: str):
        items = self.repo.get_audit_logs(flag.lower())
        return map_audit_items(items)

    
    def update_env(
        self,
        feature_name: str,
        env: str,
        request_feature: UpdateFeatureEnvDTO,
        actor: str,
    ):
        feature_name = feature_name.lower()

        raw_existing_env = self.repo.get_env(feature_name, env)
        if not raw_existing_env:
            raise AppException("Environment not found", 404)

        old = map_env_for_audit(raw_existing_env)

        self.repo.put_env(
            feature_name=feature_name,
            env=env,
            enabled=request_feature.enabled,
            rollout_end_at=request_feature.rollout_end_at,
        )

        new = {
            "environment": env,
            **request_feature.model_dump(),
        }

        publish_audit(
            feature=feature_name,
            action=AuditAction.UPDATE_ENV,
            actor=actor,
            old=old,
            new=new,
        )
