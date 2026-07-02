import { useMemo, useState } from "react";

import { requestHandoffSummary, requestPatientSummary } from "../api/summaries";
import { formatDateTime } from "../format";
import type { EvidenceItem, SummaryResponse } from "../types/summary";
import { EmptyState } from "./States";

export function SummaryPanel({ patientId }: { patientId: number }) {
  const [summary, setSummary] = useState<SummaryResponse | null>(null);
  const [busyKind, setBusyKind] = useState<"patient" | "handoff" | null>(null);
  const [error, setError] = useState<string | null>(null);

  const evidenceById = useMemo(() => {
    const pairs: Array<[string, EvidenceItem]> = summary?.evidence_package.evidence_items.map((item) => [item.id, item]) ?? [];
    return new Map<string, EvidenceItem>(pairs);
  }, [summary]);

  async function request(kind: "patient" | "handoff") {
    setBusyKind(kind);
    setError(null);
    try {
      setSummary(kind === "patient" ? await requestPatientSummary(patientId) : await requestHandoffSummary(patientId));
    } catch {
      setError("摘要產生失敗，請檢查後端服務。");
    } finally {
      setBusyKind(null);
    }
  }

  return (
    <section className="summary-panel">
      <div className="section-title">
        <div>
          <h2>Evidence-first Summary</h2>
          <p className="muted">Local-only 或 deterministic fallback；每句都必須引用 evidence ID。</p>
        </div>
        <div className="actions">
          <button className="button secondary" disabled={busyKind !== null} onClick={() => request("patient")}>
            {busyKind === "patient" ? "產生中…" : "病人摘要"}
          </button>
          <button className="button secondary" disabled={busyKind !== null} onClick={() => request("handoff")}>
            {busyKind === "handoff" ? "產生中…" : "交班摘要"}
          </button>
        </div>
      </div>
      {error && <div className="message error">{error}</div>}
      {!summary && !error && <EmptyState label="尚未產生摘要。" />}
      {summary && (
        <div className="summary-output">
          <div className="badge-row">
            <span className={`badge summary-${summary.status}`}>{summary.status}</span>
            <span className={`badge validation-${summary.validation_status}`}>{summary.validation_status}</span>
            <span className="badge prototype">{summary.adapter_mode}</span>
            <span className="badge prototype">{summary.local_only ? "LOCAL ONLY" : "NONLOCAL"}</span>
          </div>
          <dl className="meta-grid">
            <div>
              <dt>摘要類型</dt>
              <dd>{summary.summary_kind}</dd>
            </div>
            <div>
              <dt>建立時間</dt>
              <dd>{formatDateTime(summary.created_at)}</dd>
            </div>
            <div>
              <dt>模型</dt>
              <dd>{summary.model_name ?? "未使用模型"}</dd>
            </div>
            <div>
              <dt>Evidence Package</dt>
              <dd>{summary.evidence_package.package_id}</dd>
            </div>
          </dl>
          {summary.abstention_reason && (
            <div className={summary.status === "FALLBACK" ? "message success" : "message error"}>
              {summary.status === "FALLBACK" ? "Fallback 原因：" : "拒答原因："}
              {summary.abstention_reason}
            </div>
          )}
          {summary.validation_errors.length > 0 && (
            <div className="message error">驗證錯誤：{summary.validation_errors.join("；")}</div>
          )}
          {summary.sentences.length ? (
            <ol className="summary-sentences">
              {summary.sentences.map((sentence) => (
                <li key={sentence.index}>
                  <p>{sentence.text}</p>
                  <div className="citation-row">
                    {sentence.evidence_ids.map((id) => {
                      const evidence = evidenceById.get(id);
                      return (
                        <span className="citation-chip" title={evidence?.text ?? id} key={id}>
                          {id}
                        </span>
                      );
                    })}
                  </div>
                </li>
              ))}
            </ol>
          ) : (
            <EmptyState label="沒有可回傳的摘要句子。" />
          )}
        </div>
      )}
    </section>
  );
}
