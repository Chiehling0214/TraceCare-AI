import re

from app.services.evidence_package_service import EvidencePackage
from app.services.llm_adapter import GeneratedSentence


NUMBER_PATTERN = re.compile(r"(?<![\w:])-?\d+(?:\.\d+)?(?![\w:])")
EVIDENCE_TOKEN_PATTERN = re.compile(r"\b(?:patient|lab|document|fact|event|risk):\d+\b")
BANNED_LANGUAGE = [
    "diagnosis",
    "diagnosed",
    "treatment",
    "prescribe",
    "therapy",
    "診斷",
    "治療",
    "用藥建議",
    "處方",
    "requires consideration",
    "has an allergy",
]


def validate_summary_sentences(package: EvidencePackage, sentences: list[GeneratedSentence]) -> list[str]:
    errors: list[str] = []
    evidence_ids = package.evidence_ids()
    evidence_by_id = package.item_map()

    if not sentences:
        return ["SUMMARY_EMPTY"]

    for index, sentence in enumerate(sentences):
        if not sentence.text.strip():
            errors.append(f"SENTENCE_{index}_EMPTY")
        if not sentence.evidence_ids:
            errors.append(f"SENTENCE_{index}_MISSING_CITATION")
            continue
        unknown = [item for item in sentence.evidence_ids if item not in evidence_ids]
        if unknown:
            errors.append(f"SENTENCE_{index}_UNKNOWN_EVIDENCE:{','.join(unknown)}")
            continue

        mentioned_ids = set(EVIDENCE_TOKEN_PATTERN.findall(sentence.text))
        missing_mentioned_ids = sorted(mentioned_ids.difference(sentence.evidence_ids))
        if missing_mentioned_ids:
            errors.append(f"SENTENCE_{index}_MENTIONED_EVIDENCE_NOT_CITED:{','.join(missing_mentioned_ids)}")

        lower_text = sentence.text.lower()
        for banned in BANNED_LANGUAGE:
            if banned in lower_text:
                errors.append(f"SENTENCE_{index}_BANNED_LANGUAGE:{banned}")

        cited_text = " ".join(evidence_by_id[item].text for item in sentence.evidence_ids)
        cited_numbers = set(NUMBER_PATTERN.findall(cited_text))
        for number in NUMBER_PATTERN.findall(sentence.text):
            if number not in cited_numbers:
                errors.append(f"SENTENCE_{index}_NUMERIC_MISMATCH:{number}")

        cited_items = [evidence_by_id[item] for item in sentence.evidence_ids]
        cited_types = [item.type for item in cited_items]
        cited_events = [item for item in cited_items if item.type == "event"]
        if "contradict" in lower_text:
            has_contradiction_event = any(
                item.metadata.get("event_type") == "CONTRADICTION" for item in cited_events
            )
            if cited_types.count("fact") < 2 or not has_contradiction_event:
                errors.append(f"SENTENCE_{index}_UNSUPPORTED_CONTRADICTION_CLAIM")

        if "rapid increase" in lower_text or "rapid_lab_change" in lower_text:
            has_lab_event = any(
                item.metadata.get("event_type") == "RAPID_LAB_CHANGE" for item in cited_events
            )
            if cited_types.count("lab") < 2 or not has_lab_event:
                errors.append(f"SENTENCE_{index}_UNSUPPORTED_LAB_TREND_CLAIM")

    return errors
