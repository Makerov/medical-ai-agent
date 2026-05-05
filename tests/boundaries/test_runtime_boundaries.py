from pathlib import Path

import ast


PROJECT_ROOT = Path(__file__).resolve().parents[2]
BOT_MODULES = [
    PROJECT_ROOT / "app" / "bots" / "patient_bot.py",
    PROJECT_ROOT / "app" / "bots" / "doctor_bot.py",
]
FORBIDDEN_IMPORT_PREFIXES = (
    "asyncpg",
    "psycopg",
    "qdrant_client",
    "sqlalchemy",
    "openai",
    "anthropic",
    "google",
    "boto3",
)


def _imported_module_names(source_path: Path) -> set[str]:
    tree = ast.parse(source_path.read_text())
    imported_modules: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    return imported_modules


def test_bot_modules_do_not_import_storage_or_provider_sdks() -> None:
    imported_modules = {
        module_name
        for source_path in BOT_MODULES
        for module_name in _imported_module_names(source_path)
    }

    forbidden_imports = {
        module_name
        for module_name in imported_modules
        if any(
            module_name == prefix or module_name.startswith(f"{prefix}.")
            for prefix in FORBIDDEN_IMPORT_PREFIXES
        )
    }

    assert forbidden_imports == set()


def test_bot_modules_remain_thin_adapter_files() -> None:
    patient_bot_source = BOT_MODULES[0].read_text()
    doctor_bot_source = BOT_MODULES[1].read_text()

    for source in (patient_bot_source, doctor_bot_source):
        assert "postgres" not in source.lower()
        assert "qdrant" not in source.lower()
        assert "openai" not in source.lower()
        assert "anthropic" not in source.lower()
        assert "sqlalchemy" not in source.lower()
