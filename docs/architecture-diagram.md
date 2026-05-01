# Architecture Diagram

This diagram is intended to be readable as a standalone portfolio artifact.

```mermaid
flowchart LR
  Patient[Patient via Telegram] --> PatientBot[Patient Bot Adapter]
  Doctor[Doctor via Telegram] --> DoctorBot[Doctor Bot Adapter]
  PatientBot --> API[FastAPI API]
  DoctorBot --> API

  API --> Graph[LangGraph Workflow]
  Graph --> Intake[Case Intake and Consent]
  Graph --> Docs[Document Upload and Parsing]
  Graph --> Extract[Structured Extraction]
  Graph --> RAG[RAG Retrieval and Grounding]
  Graph --> Safety[Safety Validation Gate]
  Graph --> Handoff[Doctor Handoff Preparation]
  Graph --> Audit[Audit Trail and Case Artifacts]
  Graph --> Eval[Demo Exports and Minimal Eval Suite]

  Intake --> PG[(PostgreSQL)]
  Docs --> PG
  Extract --> PG
  Safety --> PG
  Handoff --> PG
  Audit --> PG

  RAG --> Qdrant[(Qdrant)]
  RAG --> Schemas[Typed Pydantic Schemas]
  Extract --> Schemas
  Safety --> Schemas
  Handoff --> Schemas

  Audit --> Artifacts[data/artifacts/<case_id>/...]
  Eval --> Artifacts
  Handoff --> Artifacts
  Graph --> Workers[Background Worker]
  Workers --> Graph

  Safety -->|blocks or corrects unsupported output| Handoff
  Handoff -->|human review required| Doctor
  Artifacts --> Reviewer[Reviewer Export Bundle]

  classDef boundary fill:#f7f2e8,stroke:#7a5c2e,color:#1f1f1f;
  classDef storage fill:#e8f1f7,stroke:#3c6e8f,color:#1f1f1f;
  classDef adapter fill:#f5e8f7,stroke:#8a4f9b,color:#1f1f1f;

  class PatientBot,DoctorBot,API,Graph,Intake,Docs,Extract,RAG,Safety,Handoff,Audit,Eval,Workers,Reviewer boundary;
  class PG,Qdrant,Artifacts storage;
  class Patient,Doctor adapter;
```

## What the diagram shows

- Patient and doctor channels are adapters, not the core system boundary.
- FastAPI is the entry point for backend operations.
- LangGraph coordinates the workflow across intake, documents, extraction, RAG, safety, and handoff.
- PostgreSQL holds case-linked state and audit records.
- Qdrant holds retrieval data separately from relational case data.
- Typed schemas sit between workflow steps so AI outputs are validated before use.
- Demo exports and reviewer bundles remain under `data/artifacts/<case_id>/...`.

## Stable location

This file lives at `docs/architecture-diagram.md` so the README can link to a stable repo-local artifact without depending on generated images or an external service.
