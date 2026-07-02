import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Protocol

from app.services.evidence_package_service import EvidencePackage


@dataclass(frozen=True)
class GeneratedSentence:
    text: str
    evidence_ids: list[str]


@dataclass(frozen=True)
class LLMGeneration:
    sentences: list[GeneratedSentence]
    adapter_mode: str
    model_name: str | None


class LocalLLMAdapter(Protocol):
    mode: str
    model_name: str | None

    def generate(self, package: EvidencePackage, summary_kind: str) -> LLMGeneration:
        ...


class DisabledLLMAdapter:
    mode = "disabled"
    model_name = None

    def generate(self, package: EvidencePackage, summary_kind: str) -> LLMGeneration:
        raise RuntimeError("Local LLM adapter is disabled.")


class FakeLLMAdapter:
    mode = "fake-test"

    def __init__(self, sentences: list[GeneratedSentence], model_name: str = "fake-test-model") -> None:
        self.sentences = sentences
        self.model_name = model_name

    def generate(self, package: EvidencePackage, summary_kind: str) -> LLMGeneration:
        return LLMGeneration(self.sentences, self.mode, self.model_name)


class OllamaLLMAdapter:
    mode = "ollama"

    def __init__(self, base_url: str, model_name: str, timeout_seconds: int = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds

    def generate(self, package: EvidencePackage, summary_kind: str) -> LLMGeneration:
        if not self.model_name:
            raise RuntimeError("LOCAL_LLM_MODEL is not configured.")

        prompt = _build_prompt(package, summary_kind)
        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=json.dumps(
                {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0, "num_predict": 320},
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except TimeoutError as exc:
            raise RuntimeError("Local Ollama generation timed out.") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError("Local Ollama runtime is unavailable.") from exc

        raw = payload.get("response", "")
        try:
            parsed = json.loads(raw)
            sentences = [
                GeneratedSentence(text=item["text"], evidence_ids=list(item["evidence_ids"]))
                for item in parsed.get("sentences", [])
            ]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise RuntimeError("Local model output failed the summary JSON contract.") from exc
        return LLMGeneration(sentences, self.mode, self.model_name)


def _build_prompt(package: EvidencePackage, summary_kind: str) -> str:
    evidence_lines = "\n".join(
        f"- {item.id} [{item.type}]: {item.text}" for item in package.evidence_items
    )
    allowed_patterns = (
        _handoff_patterns(package.patient_code)
        if summary_kind == "handoff"
        else _patient_patterns(package.patient_code)
    )
    return (
        "You are generating an evidence-first TraceCare AI prototype summary from synthetic evidence only.\n"
        "Return JSON only with this exact shape: "
        "{\"sentences\":[{\"text\":\"...\",\"evidence_ids\":[\"...\"]}]}.\n"
        "Use 3 to 5 short sentences.\n"
        f"Write in Traditional Chinese. Use the actual patient code {package.patient_code}; "
        "never output angle-bracket placeholders such as <patient_code>.\n"
        "Write conservatively. Each sentence must be a direct restatement of cited evidence only.\n"
        "Do not infer causality, contradiction, clinical meaning, diagnosis, treatment, medication advice, "
        "or actions to take.\n"
        "Do not say the patient has a condition, has an allergy, needs review, requires consideration, "
        "or requires treatment.\n"
        "Do not calculate risk, numeric changes, trends, counts, or event state.\n"
        "Do not mix lab evidence with allergy/document/fact evidence in the same sentence.\n"
        "Do not put citation tokens like lab:1 or event:2 inside sentence text; put them only in evidence_ids.\n"
        f"Allowed sentence patterns for {summary_kind} summary:\n"
        f"{allowed_patterns}"
        "Every sentence must cite evidence_ids exactly as provided below.\n"
        "If you cannot follow these rules, return {\"sentences\":[]}.\n"
        f"Summary kind: {summary_kind}\n"
        f"Evidence:\n{evidence_lines}\n"
    )


def _patient_patterns(patient_code: str) -> str:
    return (
        f"- Patient context: '{patient_code} 是本原型中的合成病人資料。'\n"
        "- Lab evidence: '摘要引用的檢驗 evidence 包含 creatinine 檢驗紀錄。'\n"
        "- Fact evidence: '摘要引用的結構化 fact evidence 來自固定格式合成臨床文件。'\n"
        "- Event evidence: '摘要引用的 event evidence 來自原型規則建立的臨床事件。'\n"
        "- Risk evidence: '摘要引用的 risk evidence 來自 Sprint 2 deterministic risk service。'\n"
    )


def _handoff_patterns(patient_code: str) -> str:
    return (
        f"- Handoff context: '{patient_code} 交班摘要只使用 TraceCare AI 的合成 evidence。'\n"
        "- Risk context: '交班摘要包含 Sprint 2 deterministic risk state，供下一位 reviewer 掌握目前原型風險狀態。'\n"
        "- Event lifecycle: '交班摘要包含 prototype event lifecycle status，供下一位 reviewer 查看事件目前狀態。'\n"
        "- Action history: '交班摘要包含已記錄的 lifecycle action history，供下一位 reviewer 追蹤已執行操作。'\n"
        "- Source availability: '交班摘要保留 lab 與 fact source evidence，供下一位 reviewer 回查來源。'\n"
    )
