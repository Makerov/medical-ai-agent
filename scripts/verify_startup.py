from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from app.core.settings import Settings, get_settings
from app.schemas.runtime_health import RuntimeProcess, StartupVerificationStatus
from app.services.runtime_health_service import RuntimeHealthService


def build_runtime_health_service(settings: Settings | None = None) -> RuntimeHealthService:
    return RuntimeHealthService(settings=settings)


def _parse_process(value: str) -> RuntimeProcess:
    return RuntimeProcess(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run startup verification checks")
    parser.add_argument(
        "--process",
        type=_parse_process,
        default=RuntimeProcess.API,
        choices=tuple(RuntimeProcess),
        help="Runtime process to verify.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = get_settings()
    service = build_runtime_health_service(settings=settings)
    report = service.verify_startup(process=args.process)
    print(json.dumps(report.model_dump(mode="json"), ensure_ascii=True, indent=2))
    return 1 if report.status == StartupVerificationStatus.BLOCKED else 0


if __name__ == "__main__":
    raise SystemExit(main())
