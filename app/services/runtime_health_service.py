from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from app.core.settings import Settings, get_settings
from app.db.postgres import (
    PostgresOperationalStateBootstrap,
    PostgresOperationalStateError,
    build_operational_state_bootstrap,
)
from app.integrations.qdrant_client import QdrantClientError, QdrantHttpClient, QdrantVectorStore
from app.schemas.runtime_health import (
    RuntimeDependencyCheck,
    RuntimeDependencyStatus,
    RuntimeLivenessResponse,
    RuntimeProcess,
    RuntimeReadinessResponse,
    RuntimeReadinessStatus,
    StartupVerificationResponse,
    StartupVerificationStatus,
    StartupVerificationStep,
    StartupVerificationStepStatus,
)

QdrantFactory = Callable[[Settings], QdrantVectorStore]
PostgresBootstrapFactory = Callable[[str], PostgresOperationalStateBootstrap]


class RuntimeHealthService:
    def __init__(
        self,
        *,
        settings: Settings | None = None,
        qdrant_client_factory: QdrantFactory | None = None,
        postgres_bootstrap_factory: PostgresBootstrapFactory | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._qdrant_client_factory = qdrant_client_factory or self._default_qdrant_factory
        self._postgres_bootstrap_factory = (
            postgres_bootstrap_factory or self._default_postgres_bootstrap_factory
        )

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

    def verify_startup(
        self,
        *,
        process: RuntimeProcess = RuntimeProcess.API,
    ) -> StartupVerificationResponse:
        steps = self._startup_verification_steps()
        blocked_steps = [
            step
            for step in steps
            if step.required and step.status == StartupVerificationStepStatus.BLOCKED
        ]
        degraded_steps = [
            step
            for step in steps
            if step.status == StartupVerificationStepStatus.DEGRADED
        ]
        reason_codes = tuple(
            reason_code
            for reason_code in (step.reason_code for step in steps)
            if reason_code is not None
        )
        if blocked_steps:
            status = StartupVerificationStatus.BLOCKED
            can_process_cases = False
        elif degraded_steps:
            status = StartupVerificationStatus.DEGRADED
            can_process_cases = True
        else:
            status = StartupVerificationStatus.PASSED
            can_process_cases = True

        return StartupVerificationResponse(
            process=process,
            status=status,
            runtime_profile=self._settings.runtime_profile,
            can_process_cases=can_process_cases,
            steps=tuple(steps),
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
            self._startup_verification_dependency(),
            self._database_dependency(),
            self._case_audit_storage_dependency(),
            self._artifact_storage_dependency(),
            self._document_storage_dependency(),
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
            self._startup_verification_dependency(),
            self._database_dependency(),
            self._case_audit_storage_dependency(),
            self._document_storage_dependency(),
            self._qdrant_dependency(),
            self._knowledge_base_storage_dependency(),
        ]

    def _operational_runtime_dependencies(self) -> list[RuntimeDependencyCheck]:
        return [
            self._required_exact_value_dependency(
                name="llm_provider",
                value=self._settings.llm_provider,
                expected_value="huggingface",
                reason_code="llm_provider_invalid",
                detail="LLM provider must be configured as huggingface.",
            ),
            self._required_value_dependency(
                name="llm_model",
                value=self._settings.llm_model,
                reason_code="llm_model_missing",
                detail="LLM model is not configured.",
            ),
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
            self._required_exact_value_dependency(
                name="ocr_provider_name",
                value=self._settings.ocr_provider_name,
                expected_value="paddleocr",
                reason_code="ocr_provider_invalid",
                detail="OCR provider must be configured as paddleocr.",
            ),
            self._required_value_dependency(
                name="ocr_model",
                value=self._settings.ocr_model,
                reason_code="ocr_model_missing",
                detail="OCR model is not configured.",
            ),
            self._required_value_dependency(
                name="ocr_lang",
                value=self._settings.ocr_lang,
                reason_code="ocr_lang_missing",
                detail="OCR language is not configured.",
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
        try:
            bootstrap = self._postgres_bootstrap_factory(database_url)
            bootstrap.verify_schema()
        except PostgresOperationalStateError as exc:
            return self._blocked_dependency(
                name="postgresql",
                reason_code=exc.code,
                detail=exc.detail,
            )
        return RuntimeDependencyCheck(
            name="postgresql",
            required=True,
            status=RuntimeDependencyStatus.READY,
        )

    def _case_audit_storage_dependency(self) -> RuntimeDependencyCheck:
        database_url = self._settings.database_url
        if not database_url or not self._is_postgresql_url(database_url):
            return self._blocked_dependency(
                name="case_audit_storage",
                reason_code="case_audit_storage_unavailable",
                detail="Case and audit PostgreSQL storage is not configured.",
            )
        try:
            bootstrap = self._postgres_bootstrap_factory(database_url)
            bootstrap.ensure_schema()
            schema_status = bootstrap.verify_schema()
        except PostgresOperationalStateError as exc:
            return self._blocked_dependency(
                name="case_audit_storage",
                reason_code=exc.code,
                detail=exc.detail,
            )

        if not schema_status.is_ready:
            return self._blocked_dependency(
                name="case_audit_storage",
                reason_code="case_audit_storage_schema_missing",
                detail="Case and audit PostgreSQL tables are not ready.",
            )
        return RuntimeDependencyCheck(
            name="case_audit_storage",
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

    def _document_storage_dependency(self) -> RuntimeDependencyCheck:
        return self._filesystem_dependency(
            name="document_storage",
            path=self._settings.artifact_root_dir,
            reason_code="document_storage_unavailable",
            detail="Document storage root is not available.",
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

    def _startup_verification_dependency(self) -> RuntimeDependencyCheck:
        report = self.verify_startup()
        if report.status == StartupVerificationStatus.BLOCKED:
            status = RuntimeDependencyStatus.BLOCKED
        elif report.status == StartupVerificationStatus.DEGRADED:
            status = RuntimeDependencyStatus.DEGRADED
        else:
            status = RuntimeDependencyStatus.READY

        reason_code = self._startup_verification_reason_code(report)
        return RuntimeDependencyCheck(
            name="startup_verification",
            required=True,
            status=status,
            reason_code=reason_code,
            detail=self._startup_verification_detail(report),
        )

    def _startup_verification_steps(self) -> list[StartupVerificationStep]:
        steps = [self._runtime_profile_step()]
        schema_dependency = self._database_dependency()
        steps.append(
            self._dependency_to_startup_step(
                schema_dependency,
                name="schema_compatibility",
            )
        )
        case_audit_storage_dependency = self._case_audit_storage_dependency()
        steps.append(
            self._dependency_to_startup_step(
                case_audit_storage_dependency,
                name="case_audit_state_schema",
            )
        )
        document_storage_dependency = self._document_storage_dependency()
        steps.append(
            self._dependency_to_startup_step(
                document_storage_dependency,
                name="document_storage",
            )
        )
        qdrant_dependency = self._qdrant_dependency()
        steps.append(
            self._dependency_to_startup_step(
                qdrant_dependency,
                name="qdrant_collection",
            )
        )
        if self._settings.runtime_profile == "operational":
            provider_dependencies = self._operational_runtime_dependencies()
            blocked_provider_dependency = next(
                (
                    dependency
                    for dependency in provider_dependencies
                    if dependency.status == RuntimeDependencyStatus.BLOCKED
                ),
                None,
            )
            steps.append(
                StartupVerificationStep(
                    name="operational_provider_config",
                    required=True,
                    status=StartupVerificationStepStatus.BLOCKED
                    if blocked_provider_dependency is not None
                    else StartupVerificationStepStatus.READY,
                    reason_code=None
                    if blocked_provider_dependency is None
                    else blocked_provider_dependency.reason_code,
                    detail=None
                    if blocked_provider_dependency is None
                    else "Operational provider configuration is incomplete.",
                )
            )
        return steps

    def _runtime_profile_step(self) -> StartupVerificationStep:
        if self._settings.runtime_profile == "operational":
            return StartupVerificationStep(
                name="runtime_profile",
                required=False,
                status=StartupVerificationStepStatus.READY,
            )
        return StartupVerificationStep(
            name="runtime_profile",
            required=False,
            status=StartupVerificationStepStatus.DEGRADED,
            reason_code="runtime_profile_local",
            detail="Runtime profile is not operational.",
        )

    def _dependency_to_startup_step(
        self,
        dependency: RuntimeDependencyCheck,
        *,
        name: str,
    ) -> StartupVerificationStep:
        status_map = {
            RuntimeDependencyStatus.READY: StartupVerificationStepStatus.READY,
            RuntimeDependencyStatus.DEGRADED: StartupVerificationStepStatus.DEGRADED,
            RuntimeDependencyStatus.BLOCKED: StartupVerificationStepStatus.BLOCKED,
        }
        return StartupVerificationStep(
            name=name,
            required=dependency.required,
            status=status_map[dependency.status],
            reason_code=dependency.reason_code,
            detail=dependency.detail,
        )

    @staticmethod
    def _startup_verification_detail(report: StartupVerificationResponse) -> str:
        if report.status == StartupVerificationStatus.PASSED:
            return "Startup verification passed."
        if report.status == StartupVerificationStatus.DEGRADED:
            return "Startup verification is degraded."
        failing_steps = [
            step.name
            for step in report.steps
            if step.required and step.status == StartupVerificationStepStatus.BLOCKED
        ]
        if failing_steps:
            joined = ", ".join(failing_steps)
            return f"Startup verification blocked at: {joined}."
        return "Startup verification blocked."

    @staticmethod
    def _startup_verification_reason_code(report: StartupVerificationResponse) -> str | None:
        blocked_steps = [
            step.reason_code
            for step in report.steps
            if step.required and step.status == StartupVerificationStepStatus.BLOCKED
        ]
        if blocked_steps:
            return next(
                (reason_code for reason_code in blocked_steps if reason_code is not None),
                None,
            )
        return report.reason_codes[0] if report.reason_codes else None

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
        if not path.is_dir():
            return self._blocked_dependency(
                name=name,
                reason_code=f"{reason_code}_not_directory",
                detail=f"{detail.rstrip('.')} Path is not a directory.",
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

    def _required_exact_value_dependency(
        self,
        *,
        name: str,
        value: object,
        expected_value: str,
        reason_code: str,
        detail: str,
    ) -> RuntimeDependencyCheck:
        if isinstance(value, str) and value.strip().lower() == expected_value:
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

    @staticmethod
    def _default_postgres_bootstrap_factory(database_url: str) -> PostgresOperationalStateBootstrap:
        return build_operational_state_bootstrap(database_url)
