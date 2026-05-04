from pathlib import Path

from app import main as app_main
from app.bots import doctor_bot, patient_bot
from app.workers import process_case_worker

PROJECT_ROOT = Path(__file__).resolve().parents[1]
COMPOSE_PATH = PROJECT_ROOT / "docker-compose.yml"


def test_runtime_scaffold_exposes_required_backend_boundaries() -> None:
    assert callable(app_main.run)
    assert callable(patient_bot.build_patient_router)
    assert callable(patient_bot.run)
    assert callable(doctor_bot.send_doctor_ready_case_delivery)
    assert callable(doctor_bot.send_doctor_case_card_delivery)
    assert hasattr(process_case_worker, "ProcessCaseWorker")


def test_runtime_topology_documents_postgresql_and_qdrant_dependencies() -> None:
    compose_text = COMPOSE_PATH.read_text(encoding="utf-8")

    assert "postgres:" in compose_text
    assert "qdrant:" in compose_text
    assert "postgres:18-alpine" in compose_text
    assert "qdrant/qdrant:" in compose_text
    assert "depends_on:" in compose_text
