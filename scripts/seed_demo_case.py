from __future__ import annotations

import argparse
import warnings
from pathlib import Path

from scripts.seed_operational_verification_case import (
    OPERATIONAL_VERIFICATION_CASE_ID,
    OPERATIONAL_VERIFICATION_FIXTURE_PATH,
    SeededOperationalVerificationCaseResult,
    load_operational_verification_fixture,
    seed_operational_verification_case,
)

DEMO_CASE_FIXTURE_PATH = OPERATIONAL_VERIFICATION_FIXTURE_PATH
DEMO_CASE_ID = OPERATIONAL_VERIFICATION_CASE_ID
SeededDemoCaseResult = SeededOperationalVerificationCaseResult


def load_demo_case_fixture(path: Path = DEMO_CASE_FIXTURE_PATH):
    return load_operational_verification_fixture(path)


def seed_demo_case(**kwargs) -> SeededDemoCaseResult:
    return seed_operational_verification_case(**kwargs)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Deprecated compatibility wrapper. "
            "Use scripts/seed_operational_verification_case.py instead."
        )
    )
    parser.add_argument("--fixture", default=str(DEMO_CASE_FIXTURE_PATH))
    parser.add_argument("--no-reset", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    warnings.warn(
        "scripts/seed_demo_case.py is deprecated; use "
        "scripts/seed_operational_verification_case.py instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    parser = build_parser()
    args = parser.parse_args(argv)
    result = seed_operational_verification_case(
        fixture_path=Path(args.fixture),
        reset_artifacts=not args.no_reset,
    )
    print(f"Seeded operational verification case {result.case_id}")
    print(f"Artifacts written under {Path('data/artifacts') / result.case_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
