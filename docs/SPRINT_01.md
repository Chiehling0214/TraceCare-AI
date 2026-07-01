# Sprint 1: Clinical Documents, Contradiction Detection, and Evidence Graph

## Status

Completed

## Background

Sprint 0 created a working end-to-end prototype around synthetic patients, creatinine labs, one deterministic rule, clinical events, evidence links, event acknowledgement/resolution, and simulated device state. The repository currently has no document model, clinical fact model, contradiction event type, graph API, or graph UI.

Sprint 1 adds a second deterministic evidence source: fixed-format synthetic clinical documents. It should prove that TraceCare AI can trace an event to multiple source types, not only labs, while keeping all clinical logic deterministic and prototype-labeled.

## Goal

Add fixed-format synthetic clinical documents, structured clinical facts for allergy statements, deterministic contradiction detection, `CONTRADICTION` clinical events, and an evidence graph that connects patients, documents, facts, labs, events, and user actions.

## User Stories

- As a demo operator, I can seed synthetic clinical documents for a patient without using real patient data.
- As a clinician reviewer, I can see that a contradiction event was created from two conflicting allergy facts.
- As a reviewer, I can inspect source document names, source sections, source offsets, and observed times for each fact.
- As a reviewer, I can see an evidence graph showing how a patient, documents, facts, labs, events, and actions relate.
- As a reviewer, I can acknowledge and resolve contradiction events through the existing human confirmation workflow.
- As a developer, I can test contradiction detection repeatedly without duplicate events.

## Scope

- Add fixed-format synthetic clinical document seed data.
- Add structured clinical facts for allergy statements.
- Support source locations such as document title, section label, line number, and character offsets.
- Add deterministic contradiction detection for allergy presence vs allergy denial in fixed-format data.
- Create `CONTRADICTION` clinical events using the existing `ClinicalEvent` lifecycle.
- Add evidence links or a backward-compatible evidence graph structure that can reference labs, documents, facts, events, and actions.
- Add an evidence graph API for one patient and for one event.
- Add Cytoscape.js to visualize graph nodes and edges in the patient detail page.
- Preserve Sprint 0 `RAPID_INCREASE` flow and existing endpoints.

## Non-goals

- No LLM.
- No embedding model.
- No vector database.
- No arbitrary PDF parsing.
- No Word/PDF upload.
- No FHIR.
- No real patient data.
- No diagnosis or treatment advice.
- No generic medical contradiction engine beyond the fixed synthetic allergy scenario.

## Dependencies

- Sprint 0 backend models and service structure.
- Existing `ClinicalEvent` and event lifecycle.
- Existing frontend patient detail page.
- Existing seed pattern in `backend/app/seed/synthetic.py`.
- Existing tests using FastAPI TestClient.

## Current Repository Assessment

Current backend:

- SQLAlchemy models exist for `Patient`, `LabResult`, `ClinicalEvent`, and `EvidenceLink`.
- `EvidenceLink` currently only has `event_id`, `lab_result_id`, and `relation_type`, so it cannot directly reference documents or facts.
- `ClinicalEvent.event_type` is a string and can hold new values such as `CONTRADICTION` without Python enum migration.
- `ClinicalEvent.severity` and `status` are strings and can continue to use `REVIEW_REQUIRED`, `HIGH_RISK`, `OPEN`, `ACKNOWLEDGED`, and `RESOLVED`.
- `rule_service.py` currently only runs `RAPID_INCREASE`; Sprint 1 should add a separate deterministic service rather than expanding lab logic in place.
- There is no migration tool; schema changes need a minimal migration strategy.
- Startup uses `create_all`, which adds new tables but does not alter existing tables.

Current frontend:

- Patient detail already fetches patient, labs, events, event details, and device state.
- Event cards already display rule ID, prototype badge, status, timestamps, and evidence comparison for lab events.
- There is no graph library or graph component.
- The custom router supports `/` and `/patients/:patientId`; Sprint 1 can keep the same route and add a section in patient detail.

Current tests:

- Backend tests cover Sprint 0 event creation and lifecycle.
- There are no tests for documents, clinical facts, graph data, or multiple event types.

Current configuration:

- Docker Compose now uses Dockerfiles and a named SQLite volume.
- Root `.env` uses backend host port `8001`; API paths should not hard-code host ports in backend code.

## Proposed Architecture Changes

- Add a `document_service` responsible for fixed-format synthetic documents and facts.
- Add a `contradiction_service` responsible for deterministic allergy contradiction analysis.
- Add a `graph_service` that returns graph nodes and edges from existing persisted records.
- Keep `rule_service.py` focused on `RAPID_INCREASE` or introduce a small analysis orchestration service that calls lab and contradiction analyzers.
- Keep existing event lifecycle functions in `event_service.py`.
- Add Cytoscape.js only to the frontend graph component, not as a global UI framework.

Minimum service boundaries:

- Document/fact persistence and seed: document service.
- Contradiction rule parameters: contradiction service configuration object.
- Graph response construction: graph service.
- API routes: add routes without changing existing Sprint 0 routes.

## Proposed Data Model Changes

Add new tables or equivalent SQLAlchemy models:

### ClinicalDocument

- `id`
- `patient_id`
- `document_type`
- `title`
- `source_document`
- `authored_at`
- `created_at`
- `is_synthetic`

### ClinicalFact

- `id`
- `patient_id`
- `document_id`
- `fact_type`
- `subject`
- `polarity`
- `value`
- `status`
- `source_section`
- `source_line`
- `source_start_char`
- `source_end_char`
- `observed_at`
- `created_at`

Initial Sprint 1 fact values:

- `fact_type`: `ALLERGY_STATEMENT`
- `subject`: medication or allergen name, e.g. `penicillin`
- `polarity`: `PRESENT` or `NEGATED`
- `status`: `ACTIVE`, `DENIED`, or `UNKNOWN`

### Evidence Graph Model

Preferred minimal approach for Sprint 1:

- Do not replace existing `EvidenceLink`.
- Add a graph response service that derives nodes/edges from `Patient`, `LabResult`, `ClinicalDocument`, `ClinicalFact`, `ClinicalEvent`, and `EvidenceLink`.
- Add document/fact event evidence through either:
  - a new `EventEvidence` table with typed target fields, or
  - a new nullable `clinical_fact_id` column/table relationship if migration is simple.

Recommended minimal table:

### EventEvidence

- `id`
- `event_id`
- `target_type`
- `target_id`
- `relation_type`
- `created_at`

Relation types:

- `SUPPORTS`
- `CONTRADICTS`
- `SOURCE_DOCUMENT`
- `ASSERTED_FACT`
- `DENIED_FACT`

Compatibility note:

- Existing `EvidenceLink` remains in place for Sprint 0 lab evidence.
- Event detail for `RAPID_LAB_CHANGE` should continue to return the existing evidence shape.
- New graph APIs can use a new graph-specific response shape.

## Proposed API Changes

Add:

- `GET /api/patients/{patient_id}/documents`
- `GET /api/documents/{document_id}`
- `GET /api/patients/{patient_id}/facts`
- `POST /api/prototype/run-contradiction-analysis`
- `GET /api/patients/{patient_id}/evidence-graph`
- `GET /api/events/{event_id}/evidence-graph`

Extend:

- `GET /api/patients/{patient_id}/events` can return both `RAPID_LAB_CHANGE` and `CONTRADICTION`.
- `GET /api/events/{event_id}` should remain backward-compatible. For contradiction events, include a graph/evidence summary without breaking lab event fields.

Example graph response shape:

```json
{
  "nodes": [
    {"id": "patient:1", "type": "patient", "label": "P001"},
    {"id": "document:1", "type": "document", "label": "Synthetic admission note"},
    {"id": "fact:1", "type": "fact", "label": "Penicillin allergy present"},
    {"id": "event:2", "type": "event", "label": "Contradictory allergy statements"}
  ],
  "edges": [
    {"id": "edge:1", "source": "patient:1", "target": "document:1", "relation": "HAS_DOCUMENT"},
    {"id": "edge:2", "source": "document:1", "target": "fact:1", "relation": "CONTAINS_FACT"},
    {"id": "edge:3", "source": "fact:1", "target": "event:2", "relation": "SUPPORTS"}
  ]
}
```

## Proposed UI Changes

- Add a documents/facts section to patient detail.
- Add contradiction event cards using the existing `ClinicalEventCard` pattern.
- Add an evidence graph panel below event list or as a detail section.
- Add Cytoscape.js graph rendering with:
  - node type legend,
  - selected node detail panel,
  - source document/time/position display,
  - no medical diagnosis language.
- Add loading, empty, and error states for documents, facts, and graph.
- Keep patient overview layout stable; only event counts/severity may change when contradiction events exist.

## Synthetic Test Data

Add at least:

### P001

- Existing creatinine labs remain unchanged.
- Document A: admission note stating `Allergy: Penicillin`.
- Document B: medication reconciliation stating `No known allergy to penicillin`.
- Expected: one `CONTRADICTION` event.

### P002

- Document A: `No known drug allergies`.
- Document B: `No known drug allergies`.
- Expected: no contradiction event.

### P003

- One document with one allergy statement.
- Expected: insufficient facts or no contradiction event.

Each document must include:

- source document filename,
- authored time,
- section label,
- line number,
- character offsets or equivalent source position.

## Tasks

1. Add SQLAlchemy models for synthetic documents, facts, and typed event evidence or graph evidence.
2. Add Pydantic schemas for documents, facts, contradiction analysis, and graph responses.
3. Add repeatable synthetic document/fact seed data.
4. Add deterministic allergy contradiction service.
5. Add duplicate prevention for contradiction events.
6. Add graph service that returns nodes/edges for patient and event.
7. Add API routes for documents, facts, contradiction analysis, and graph retrieval.
8. Add backend tests for seed idempotency, P001 contradiction trigger, P002/P003 no-trigger, duplicate prevention, event detail, graph nodes/edges, and 404s.
9. Add Cytoscape.js dependency to frontend.
10. Add graph API client/types.
11. Add document/fact list components.
12. Add graph component with selected node details.
13. Update patient detail page to show documents/facts/graph.
14. Update docs/API_SPEC.md or add Sprint 1 API addendum after implementation.

## Expected Files

Expected backend files:

- `backend/app/models/clinical_document.py`
- `backend/app/models/clinical_fact.py`
- `backend/app/models/event_evidence.py` or equivalent
- `backend/app/schemas/document.py`
- `backend/app/schemas/fact.py`
- `backend/app/schemas/graph.py`
- `backend/app/services/document_service.py`
- `backend/app/services/contradiction_service.py`
- `backend/app/services/graph_service.py`
- `backend/app/seed/synthetic_documents.py` or merged seed module
- `backend/tests/test_sprint_01_documents.py`
- `backend/tests/test_sprint_01_graph.py`

Expected frontend files:

- `frontend/src/api/documents.ts`
- `frontend/src/api/graph.ts`
- `frontend/src/types/document.ts`
- `frontend/src/types/graph.ts`
- `frontend/src/components/ClinicalDocumentsPanel.tsx`
- `frontend/src/components/ClinicalFactsPanel.tsx`
- `frontend/src/components/EvidenceGraphPanel.tsx`

Expected docs after implementation:

- API addendum or updated `docs/API_SPEC.md`
- Updated `docs/DATA_MODEL.md`
- Updated `docs/PROTOTYPE_RULES.md`

## Migration Strategy

Because Sprint 0 has no migration tool, Sprint 1 should introduce the smallest safe migration approach:

- For local demo, new tables can be created through `Base.metadata.create_all`.
- Existing tables must not be dropped.
- Existing Sprint 0 seed data must remain valid.
- If adding a generic evidence table, keep old `EvidenceLink` for lab evidence.
- Document a reset path for local demo data if schema changes require a fresh SQLite database.

Recommended but optional:

- Introduce Alembic only if the team expects persistent demo databases across sprints.
- If Alembic is deferred, clearly document that schema migration is reset-based for prototype data.

## Testing Plan

Backend tests:

- Health still returns 200.
- Existing Sprint 0 tests remain passing.
- Synthetic documents seed idempotently.
- P001 contradiction analysis creates exactly one `CONTRADICTION` event.
- P002 does not create a contradiction.
- P003 does not create a contradiction due to insufficient/conflict-free facts.
- Re-running contradiction analysis skips duplicate events.
- Contradiction event evidence includes both conflicting facts and source documents.
- Graph API returns patient/document/fact/event nodes.
- Graph API returns source-position edges.
- Unknown document/fact/event graph resources return 404.

Frontend checks:

- Patient detail shows documents and facts.
- Contradiction event appears in event list.
- Graph renders non-empty nodes/edges for P001.
- Selecting a graph node shows source metadata.
- Loading, empty, and error states are visible.

## Acceptance Criteria

- P001 has fixed-format synthetic documents with conflicting allergy facts.
- Running contradiction analysis creates one `CONTRADICTION` event.
- The event is traceable to both conflicting facts and their source documents.
- P002 and P003 do not create false contradiction events.
- Existing Sprint 0 lab analysis still works.
- Existing acknowledge/resolve workflow works for contradiction events.
- Evidence graph API returns useful nodes and edges.
- Cytoscape graph is visible on patient detail.
- All new and existing backend tests pass.
- No LLM, embeddings, vector database, arbitrary PDF parsing, or real patient data is introduced.

## Risks and Mitigations

- Risk: Evidence model becomes too broad too early.
  - Mitigation: add minimal typed event evidence or graph service while preserving existing `EvidenceLink`.
- Risk: Graph UI becomes cluttered.
  - Mitigation: start with patient/document/fact/event nodes only and a selected-node details panel.
- Risk: Contradiction detector is mistaken for clinical diagnosis.
  - Mitigation: label all outputs as `Prototype Rule`; use "requires review" language only.
- Risk: Schema changes break Sprint 0 data.
  - Mitigation: additive tables only; keep existing APIs stable.
- Risk: Cytoscape dependency increases frontend complexity.
  - Mitigation: isolate it in one component and keep data shape simple.

## Definition of Done

- Sprint 0 demo flow remains runnable.
- Synthetic documents and facts are seeded idempotently.
- Contradiction analysis is deterministic and duplicate-safe.
- `CONTRADICTION` events use human confirmation lifecycle.
- Evidence graph API and UI show traceable source relationships.
- Tests cover positive, negative, duplicate, and graph cases.
- Documentation is updated to reflect actual implemented APIs and models.

## Implemented

- Added additive SQLAlchemy models: `ClinicalDocument`, `ClinicalFact`, and `EventEvidence`.
- Added fixed-format synthetic document and allergy fact seed data for P001, P002, and P003.
- Added deterministic `ALLERGY_CONTRADICTION` rule service.
- Added duplicate-safe `CONTRADICTION` event creation using typed evidence.
- Added document/fact APIs and patient/event evidence graph APIs.
- Extended event detail with `document_evidence` while preserving Sprint 0 lab `evidence`.
- Added frontend document, fact, and Cytoscape evidence graph panels to patient detail.
- Updated overview analysis flow to run both Sprint 0 lab analysis and Sprint 1 contradiction analysis.
- Added Sprint 1 backend tests for seed, APIs, contradiction detection, duplicate prevention, lifecycle, graph responses, and 404/422 behavior.

## Acceptance Results

- P001 has fixed-format synthetic documents with conflicting allergy facts: PASS.
- Running contradiction analysis creates one `CONTRADICTION` event: PASS.
- The event is traceable to both conflicting facts and their source documents: PASS.
- P002 and P003 do not create false contradiction events: PASS.
- Existing Sprint 0 lab analysis still works: PASS.
- Existing acknowledge/resolve workflow works for contradiction events: PASS.
- Evidence graph API returns useful nodes and edges: PASS.
- Cytoscape graph is visible on patient detail: PASS by successful type/build validation; browser visual QA not captured in this document.
- All new and existing backend tests pass: PASS.
- No LLM, embeddings, vector database, arbitrary PDF parsing, or real patient data is introduced: PASS.

## Test Results

- Backend: `20 passed, 2 warnings`.
- Frontend type check: passed.
- Frontend production build: passed.
- Local smoke on Sprint 1 server: patients `3`, lab events created `1`, contradiction events created `1`, P001 graph `9` nodes and `18` edges.
- Warnings: FastAPI `on_event` deprecation warnings remain from Sprint 0 startup code.

## Deviations

- Alembic was not introduced. Sprint 1 uses the documented minimal prototype migration path: additive tables through SQLAlchemy `create_all`.
- The evidence graph is derived by a service from persisted records rather than persisted as a separate graph table.
- Cytoscape is dynamically imported inside the graph panel so it does not inflate the initial application chunk.

## Technical Decisions

- `EvidenceLink` remains lab-only for Sprint 0 backward compatibility.
- `EventEvidence` stores typed targets using `target_type` and `target_id` for Sprint 1 document/fact evidence.
- `ALLERGY_CONTRADICTION` compares only fixed-format structured facts with the same patient and subject.
- Event graph edge direction is source-to-derived artifact: patient to document/lab/event, document to fact, fact/lab/document to event.

## Known Issues

- Existing SQLite databases may need restart/reset if created before Sprint 1 tables existed; no destructive migration is run automatically.
- The frontend has no automated browser/e2e test suite yet.
- FastAPI startup still uses deprecated `on_event`; this is pre-existing and not part of Sprint 1 scope.

## Next Sprint Dependency

Sprint 2 depends on Sprint 1 producing stable event types and graph/evidence identifiers for `CONTRADICTION`. Risk fusion should not begin until contradiction events can be created, acknowledged, resolved, and traced to source evidence.
