import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import SummaryRecord
from app.services.errors import api_error
from app.services.evidence_package_service import EvidencePackage, build_evidence_package
from app.services.llm_adapter import (
    DisabledLLMAdapter,
    GeneratedSentence,
    LLMGeneration,
    LocalLLMAdapter,
    OllamaLLMAdapter,
)
from app.services.summary_validator import validate_summary_sentences


def generate_summary(
    db: Session,
    patient_id: int,
    summary_kind: str,
    adapter: LocalLLMAdapter | None = None,
    prefer_llm: bool = True,
) -> dict[str, object]:
    package = build_evidence_package(db, patient_id, summary_kind)
    now = datetime.now(timezone.utc)

    if not package.sufficient:
        record = _save_record(
            db,
            package=package,
            status="ABSTAINED",
            validation_status="ABSTAINED",
            adapter_mode="none",
            model_name=None,
            sentences=[],
            validation_errors=[],
            abstention_reason=package.insufficiency_reason,
            created_at=now,
        )
        return _record_payload(record)

    selected_adapter = adapter or _adapter_from_settings()
    if isinstance(selected_adapter, DisabledLLMAdapter) or not prefer_llm:
        generation = _deterministic_fallback(package)
        status = "FALLBACK"
    else:
        try:
            generation = selected_adapter.generate(package, summary_kind)
            status = "GENERATED"
        except RuntimeError as exc:
            generation = _deterministic_fallback(package)
            status = "FALLBACK"
            fallback_reason = str(exc)
            record = _save_validated_generation(db, package, generation, status, now, fallback_reason)
            return _record_payload(record)

    record = _save_validated_generation(db, package, generation, status, now)
    return _record_payload(record)


def get_summary(db: Session, summary_id: str) -> dict[str, object]:
    return _record_payload(_get_record_or_404(db, summary_id))


def get_summary_evidence(db: Session, summary_id: str) -> dict[str, object]:
    record = _get_record_or_404(db, summary_id)
    return {"summary_id": record.id, "evidence_package": json.loads(record.evidence_package_json)}


def _save_validated_generation(
    db: Session,
    package: EvidencePackage,
    generation: LLMGeneration,
    status: str,
    created_at: datetime,
    fallback_reason: str | None = None,
) -> SummaryRecord:
    validation_errors = validate_summary_sentences(package, generation.sentences)
    if validation_errors and status == "GENERATED":
        fallback_generation = _deterministic_fallback(package)
        fallback_errors = validate_summary_sentences(package, fallback_generation.sentences)
        return _save_record(
            db,
            package=package,
            status="FALLBACK" if not fallback_errors else "REJECTED",
            validation_status="PASSED" if not fallback_errors else "FAILED",
            adapter_mode=fallback_generation.adapter_mode,
            model_name=None,
            sentences=fallback_generation.sentences if not fallback_errors else [],
            validation_errors=fallback_errors,
            abstention_reason="LLM_OUTPUT_VALIDATION_FAILED_FALLBACK_USED" if not fallback_errors else "SUMMARY_VALIDATION_FAILED",
            created_at=created_at,
        )
    final_status = "REJECTED" if validation_errors else status
    validation_status = "FAILED" if validation_errors else "PASSED"
    abstention_reason = fallback_reason if final_status == "FALLBACK" else None
    if validation_errors:
        abstention_reason = "SUMMARY_VALIDATION_FAILED"
    return _save_record(
        db,
        package=package,
        status=final_status,
        validation_status=validation_status,
        adapter_mode=generation.adapter_mode,
        model_name=generation.model_name,
        sentences=generation.sentences if not validation_errors else [],
        validation_errors=validation_errors,
        abstention_reason=abstention_reason,
        created_at=created_at,
    )


def _deterministic_fallback(package: EvidencePackage) -> LLMGeneration:
    if package.summary_kind == "handoff":
        return _handoff_fallback(package)
    return _patient_fallback(package)


def _patient_fallback(package: EvidencePackage) -> LLMGeneration:
    evidence = package.item_map()
    labs = [item for item in package.evidence_items if item.type == "lab"]
    facts = [item for item in package.evidence_items if item.type == "fact"]
    events = [item for item in package.evidence_items if item.type == "event"]
    risk = [item for item in package.evidence_items if item.type == "risk"]
    patient = evidence[f"patient:{package.patient_id}"]

    sentences = [
        GeneratedSentence(
            text=f"{package.patient_code} 是本原型中的合成病人資料。",
            evidence_ids=[patient.id],
        )
    ]
    if labs:
        sentences.append(
            GeneratedSentence(
                text="摘要引用的檢驗 evidence 包含 creatinine 檢驗紀錄。",
                evidence_ids=[item.id for item in labs],
            )
        )
    if facts:
        sentences.append(
            GeneratedSentence(
                text="摘要引用的結構化 fact evidence 來自固定格式合成臨床文件。",
                evidence_ids=[item.id for item in facts],
            )
        )
    if events:
        sentences.append(
            GeneratedSentence(
                text="摘要引用的 event evidence 來自原型規則建立的臨床事件。",
                evidence_ids=[item.id for item in events],
            )
        )
    if risk:
        sentences.append(
            GeneratedSentence(
                text="摘要引用的 risk evidence 來自 Sprint 2 deterministic risk service。",
                evidence_ids=[risk[0].id],
            )
        )
    return LLMGeneration(sentences, "deterministic-fallback", None)


def _handoff_fallback(package: EvidencePackage) -> LLMGeneration:
    evidence = package.item_map()
    risk = [item for item in package.evidence_items if item.type == "risk"]
    events = [item for item in package.evidence_items if item.type == "event"]
    actions = [item for item in package.evidence_items if item.type == "action"]
    labs = [item for item in package.evidence_items if item.type == "lab"]
    facts = [item for item in package.evidence_items if item.type == "fact"]
    patient = evidence[f"patient:{package.patient_id}"]

    sentences = [
        GeneratedSentence(
            text=f"{package.patient_code} 交班摘要只使用 TraceCare AI 的合成 evidence。",
            evidence_ids=[patient.id],
        )
    ]
    if risk:
        sentences.append(
            GeneratedSentence(
                text="交班摘要包含 Sprint 2 deterministic risk state，供下一位 reviewer 掌握目前原型風險狀態。",
                evidence_ids=[risk[0].id],
            )
        )
    if events:
        sentences.append(
            GeneratedSentence(
                text="交班摘要包含 prototype event lifecycle status，供下一位 reviewer 查看事件目前狀態。",
                evidence_ids=[item.id for item in events],
            )
        )
    if actions:
        sentences.append(
            GeneratedSentence(
                text="交班摘要包含已記錄的 lifecycle action history，供下一位 reviewer 追蹤已執行操作。",
                evidence_ids=[item.id for item in actions],
            )
        )
    if labs or facts:
        sentences.append(
            GeneratedSentence(
                text="交班摘要保留 lab 與 fact source evidence，供下一位 reviewer 回查來源。",
                evidence_ids=[item.id for item in [*labs, *facts]],
            )
        )
    return LLMGeneration(sentences, "deterministic-fallback", None)


def _adapter_from_settings() -> LocalLLMAdapter:
    settings = get_settings()
    if settings.llm_mode == "ollama":
        return OllamaLLMAdapter(
            settings.local_llm_base_url,
            settings.local_llm_model,
            timeout_seconds=settings.local_llm_timeout_seconds,
        )
    return DisabledLLMAdapter()


def _save_record(
    db: Session,
    package: EvidencePackage,
    status: str,
    validation_status: str,
    adapter_mode: str,
    model_name: str | None,
    sentences: list[GeneratedSentence],
    validation_errors: list[str],
    abstention_reason: str | None,
    created_at: datetime,
) -> SummaryRecord:
    record = SummaryRecord(
        id=str(uuid4()),
        patient_id=package.patient_id,
        summary_kind=package.summary_kind,
        status=status,
        validation_status=validation_status,
        adapter_mode=adapter_mode,
        model_name=model_name,
        local_only="true",
        text=" ".join(sentence.text for sentence in sentences),
        sentences_json=json.dumps(
            [
                {"index": index, "text": sentence.text, "evidence_ids": sentence.evidence_ids}
                for index, sentence in enumerate(sentences)
            ]
        ),
        evidence_package_json=json.dumps(package.as_dict()),
        validation_errors_json=json.dumps(validation_errors),
        abstention_reason=abstention_reason,
        created_at=created_at,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def _get_record_or_404(db: Session, summary_id: str) -> SummaryRecord:
    record = db.get(SummaryRecord, summary_id)
    if record is None:
        raise api_error(404, "SUMMARY_NOT_FOUND", f"Summary {summary_id} was not found.")
    return record


def _record_payload(record: SummaryRecord) -> dict[str, object]:
    package = json.loads(record.evidence_package_json)
    return {
        "id": record.id,
        "patient_id": record.patient_id,
        "patient_code": package["patient_code"],
        "summary_kind": record.summary_kind,
        "status": record.status,
        "validation_status": record.validation_status,
        "adapter_mode": record.adapter_mode,
        "model_name": record.model_name,
        "local_only": record.local_only == "true",
        "text": record.text,
        "sentences": json.loads(record.sentences_json),
        "evidence_package": package,
        "validation_errors": json.loads(record.validation_errors_json),
        "abstention_reason": record.abstention_reason,
        "created_at": record.created_at,
    }
