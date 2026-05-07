from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.core.settings import Settings, get_settings
from app.integrations.qdrant_client import QdrantClientError, QdrantHttpClient, QdrantVectorStore
from app.schemas.runtime_health import (
    RuntimeDependencyCheck,
    RuntimeDependencyStatus,
    RuntimeLivenessResponse,
    RuntimeProcess,
    RuntimeReadinessResponse,
    RuntimeReadinessStatus,
)

QdrantFactory = Callable[[Settings], QdrantVectorStore]


class RuntimeHealthService:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        qdrant_client_factory: QdrantFactory | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._qdrant_client_factory = qdrant_client_factory or self._default_qdrant_factory

    def build_liveness(
        self,
        *,
        process: RuntimeProcess = RuntimeProcess.API,
    ) -> RuntimeLivenessResponse:
        return RuntimeLivenessResponse(
            process=process,
            service=self._settings.app_name,
            environment=self._settings.environment,
            runtime_profile=self._settings.runtime_profile,
        )

    def evaluate_readiness(
        self,
        *,
        process: RuntimeProcess = RuntimeProcess.API,
    ) -> RuntimeReadinessResponse:
        dependencies = self._dependencies_for_process(process)
        blocking_dependencies = [
            dependency
            for dependency in dependencies
            if dependency.status == RuntimeDependencyStatus.BLOCKED
        ]
        degraded_dependencies = [
            dependency
            for dependency in dependencies
            if dependency.status == RuntimeDependencyStatus.DEGRADED
        ]

        reason_codes = tuple(
            reason_code
            for reason_code in (dependency.reason_code for dependency in dependencies)
            if reason_code is not None
        )
        if blocking_dependencies:
            status = RuntimeReadinessStatus.NOT_READY
        elif degraded_dependencies or self._settings.runtime_profile != "operational":
            status = RuntimeReadinessStatus.DEGRADED
            if (
                self._settings.runtime_profile != "operational"
                and "runtime_profile_local" not in reason_codes
            ):
                reason_codes = reason_codes + ("runtime_profile_local",)
        else:
            status = RuntimeReadinessStatus.READY

        return RuntimeReadinessResponse(
            process=process,
            status=status,
            runtime_profile=self._settings.runtime_profile,
            dependencies=tuple(dependencies),
            reason_codes=reason_codes,
        )

    def _dependencies_for_process(self, process: RuntimeProcess) -> list[RuntimeDependencyCheck]:
        dependencies = [self._settings_loaded_dependency()]
        match process:
            case RuntimeProcess.API:
                dependencies.extend(self._api_dependencies())
            case RuntimeProcess.PATIENT_BOT:
                dependencies.extend(self._patient_bot_dependencies())
            case RuntimeProcess.DOCTOR_BOT:
                dependencies.extend(self._doctor_bot_dependencies())
            case RuntimeProcess.WORKER:
                dependencies.extend(self._worker_dependencies())
        return dependencies

    def _api_dependencies(self) -> list[RuntimeDependencyCheck]:
        dependencies = [
            self._database_dependency(),
            self._artifact_storage_dependency(),
            self._knowledge_base_storage_dependency(),
            self._qdrant_dependency(),
        ]
        if self._settings.runtime_profile == "operational":
            dependencies.extend(self._operational_runtime_dependencies())
        return dependencies

    def _patient_bot_dependencies(self) -> list[RuntimeDependencyCheck]:
        return [
            self._required_value_dependency(
                name="patient_bot_token",
                value=self._settings.patient_bot_token,
                reason_code="patient_bot_token_missing",
                detail="Patient bot token is not configured.",
            ),
        ]

    def _doctor_bot_dependencies(self) -> list[RuntimeDependencyCheck]:
        dependencies = [
            self._required_value_dependency(
                name="doctor_bot_token",
                value=self._settings.doctor_bot_token,
                reason_code="doctor_bot_token_missing",
                detail="Doctor bot token is not configured.",
            ),
            self._required_value_dependency(
                name="doctor_telegram_id_allowlist",
                value=self._settings.doctor_telegram_id_allowlist,
                reason_code="doctor_allowlist_missing",
                detail="Doctor allowlist is empty.",
            ),
        ]
        return dependencies

    def _worker_dependencies(self) -> list[RuntimeDependencyCheck]:
        return [
            self._database_dependency(),
            self._qdrant_dependency(),
            self._knowledge_base_storage_dependency(),
        ]

    def _operational_runtime_dependencies(self) -> list[RuntimeDependencyCheck]:
        return [
            self._required_value_dependency(
                name="hf_token",
                value=self._settings.hf_token,
                reason_code="hf_token_missing",
                detail="HF token is not configured.",
            ),
            self._required_value_dependency(
                name="patient_bot_token",
                value=self._settings.patient_bot_token,
                reason_code="patient_bot_token_missing",
                detail="Patient bot token is not configured.",
            ),
            self._required_value_dependency(
                name="doctor_bot_token",
                value=self._settings.doctor_bot_token,
                reason_code="doctor_bot_token_missing",
                detail="Doctor bot token is not configured.",
            ),
            self._required_value_dependency(
                name="ocr_provider_name",
                value=self._settings.ocr_provider_name,
                reason_code="ocr_provider_missing",
                detail="OCR provider is not configured.",
            ),
        ]

    def _settings_loaded_dependency(self) -> RuntimeDependencyCheck:
        return RuntimeDependencyCheck(
            name="settings",
            required=True,
            status=RuntimeDependencyStatus.READY,
        )

    def _database_dependency(self) -> RuntimeDependencyCheck:
        database_url = self._settings.database_url
        if not database_url:
            return self._blocked_dependency(
                name="postgresql",
                reason_code="database_url_missing",
                detail="Database URL is not configured.",
            )
        if not self._is_postgresql_url(database_url):
            return self._blocked_dependency(
                name="postgresql",
                reason_code="database_url_invalid",
                detail="Database URL must point to PostgreSQL.",
            )
        return RuntimeDependencyCheck(
            name="postgresql",
            required=True,
            status=RuntimeDependencyStatus.READY,
        )

    def _artifact_storage_dependency(self) -> RuntimeDependencyCheck:
        return self._filesystem_dependency(
            name="artifact_storage",
            path=self._settings.artifact_root_dir,
            reason_code="artifact_root_dir_missing",
            detail="Artifact storage directory does not exist.",
        )

    def _knowledge_base_storage_dependency(self) -> RuntimeDependencyCheck:
        return self._filesystem_dependency(
            name="knowledge_base_storage",
            path=self._settings.knowledge_base_seed_dir,
            reason_code="knowledge_base_seed_dir_missing",
            detail="Knowledge base seed directory does not exist.",
        )

    def _qdrant_dependency(self) -> RuntimeDependencyCheck:
        if not self._settings.qdrant_url:
            return self._blocked_dependency(
                name="qdrant",
                reason_code="qdrant_url_missing",
                detail="Qdrant URL is not configured.",
            )

        client = self._qdrant_client_factory(self._settings)
        try:
            collection_exists = client.collection_exists(self._settings.qdrant_collection_name)
        except QdrantClientError as exc:
            reason_code = {
                "connection_failed": "qdrant_unreachable",
                "collection_not_found": "qdrant_collection_missing",
                "not_found": "qdrant_collection_missing",
            }.get(exc.code, "qdrant_unavailable")
            return self._blocked_dependency(
                name="qdrant",
                reason_code=reason_code,
                detail="Qdrant collection check failed.",
            )

        if not collection_exists:
            return self._blocked_dependency(
                name="qdrant",
                reason_code="qdrant_collection_missing",
                detail="Qdrant collection is not available.",
            )
        return RuntimeDependencyCheck(
            name="qdrant",
            required=True,
            status=RuntimeDependencyStatus.READY,
        )

    def _filesystem_dependency(
        self,
        *,
        name: str,
        path: Path,
        reason_code: str,
        detail: str,
    ) -> RuntimeDependencyCheck:
        if not path.exists():
            return self._blocked_dependency(
                name=name,
                reason_code=reason_code,
                detail=detail,
            )
        return RuntimeDependencyCheck(
            name=name,
            required=True,
            status=RuntimeDependencyStatus.READY,
        )

    def _required_value_dependency(
        self,
        *,
        name: str,
        value: object,
        reason_code: str,
        detail: str,
    ) -> RuntimeDependencyCheck:
        if self._is_truthy_value(value):
            return RuntimeDependencyCheck(
                name=name,
                required=True,
                status=RuntimeDependencyStatus.READY,
            )
        return self._blocked_dependency(
            name=name,
            reason_code=reason_code,
            detail=detail,
        )

    def _blocked_dependency(
        self,
        *,
        name: str,
        reason_code: str,
        detail: str,
    ) -> RuntimeDependencyCheck:
        return RuntimeDependencyCheck(
            name=name,
            required=True,
            status=RuntimeDependencyStatus.BLOCKED,
            reason_code=reason_code,
            detail=detail,
        )

    @staticmethod
    def _is_truthy_value(value: object) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        if isinstance(value, (tuple, list, set, dict)):
            return bool(value)
        return bool(value)

    @staticmethod
    def _is_postgresql_url(value: str) -> bool:
        normalized = value.strip().lower()
        return normalized.startswith("postgresql://") or normalized.startswith("postgresql+")

    @staticmethod
    def _default_qdrant_factory(settings: Settings) -> QdrantVectorStore:
        return QdrantHttpClient(
            base_url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )
