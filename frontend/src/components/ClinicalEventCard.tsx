import { acknowledgeEvent, deferEvent, fetchEvent, resolveEvent } from "../api/events";
import { formatDateTime } from "../format";
import type { ClinicalEvent, EventDetail } from "../types/event";
import { EvidenceComparison } from "./EvidenceComparison";
import { EventStatusBadge, RiskBadge } from "./StatusBadges";

interface Props {
  event: ClinicalEvent;
  detail: EventDetail | null;
  busyEventId: number | null;
  onDetailLoaded: (detail: EventDetail) => void;
  onChanged: (message: string) => Promise<void>;
  setBusyEventId: (id: number | null) => void;
}

export function ClinicalEventCard({ event, detail, busyEventId, onDetailLoaded, onChanged, setBusyEventId }: Props) {
  async function ensureDetail() {
    if (!detail) onDetailLoaded(await fetchEvent(event.id));
  }

  async function handleAcknowledge() {
    setBusyEventId(event.id);
    try {
      await acknowledgeEvent(event.id);
      await onChanged("事件已確認，仍需後續處理。");
    } finally {
      setBusyEventId(null);
    }
  }

  async function handleResolve() {
    setBusyEventId(event.id);
    try {
      await resolveEvent(event.id);
      await onChanged("事件已結案。");
    } finally {
      setBusyEventId(null);
    }
  }

  async function handleDefer() {
    setBusyEventId(event.id);
    try {
      await deferEvent(event.id, { reason: "Prototype reviewer deferred follow-up" });
      await onChanged("事件已延後，仍會保留在未結案清單。");
    } finally {
      setBusyEventId(null);
    }
  }

  return (
    <article className="event-card" onMouseEnter={ensureDetail}>
      <div className="event-header">
        <div>
          <div className="badge-row">
            <RiskBadge value={event.severity} />
            <EventStatusBadge value={event.status} />
            <span className="badge prototype">Prototype Rule</span>
          </div>
          <h3>{event.title}</h3>
        </div>
        <span className="code">{event.rule_id}</span>
      </div>
      <p>{event.description}</p>
      <dl className="meta-grid">
        <div>
          <dt>事件類型</dt>
          <dd>{event.event_type}</dd>
        </div>
        <div>
          <dt>建立時間</dt>
          <dd>{formatDateTime(event.created_at)}</dd>
        </div>
        <div>
          <dt>確認時間</dt>
          <dd>{formatDateTime(event.acknowledged_at)}</dd>
        </div>
        <div>
          <dt>延後到期</dt>
          <dd>{formatDateTime(event.deferred_until)}</dd>
        </div>
        <div>
          <dt>升級時間</dt>
          <dd>{formatDateTime(event.escalated_at)}</dd>
        </div>
        <div>
          <dt>結案時間</dt>
          <dd>{formatDateTime(event.resolved_at)}</dd>
        </div>
      </dl>
      {event.escalation_reason && <p className="analysis-line">升級原因：{event.escalation_reason}</p>}
      {detail?.analysis && (
        <p className="analysis-line">
          Evidence: {detail.analysis.previous_value} → {detail.analysis.current_value} {detail.analysis.unit}，
          時間差 {detail.analysis.time_difference_hours} 小時
        </p>
      )}
      {detail ? <EvidenceComparison detail={detail} /> : <button className="link-button" onClick={ensureDetail}>載入 evidence</button>}
      {detail && (
        <section className="action-history">
          <div className="section-title compact">
            <h3>Action History</h3>
            <span className="muted">{detail.action_history.length} 筆</span>
          </div>
          {detail.action_history.length ? (
            <ol>
              {detail.action_history.map((action) => (
                <li key={action.id}>
                  <strong>{action.action_type}</strong>
                  <span>{formatDateTime(action.created_at)}</span>
                  <span>{action.actor_label}</span>
                  {action.note && <p>{action.note}</p>}
                </li>
              ))}
            </ol>
          ) : (
            <p className="muted">尚無操作紀錄。</p>
          )}
        </section>
      )}
      <div className="actions">
        {(event.status === "OPEN" || event.status === "DEFERRED") && (
          <button className="button" disabled={busyEventId === event.id} onClick={handleAcknowledge}>
            {busyEventId === event.id ? "處理中…" : "確認事件"}
          </button>
        )}
        {event.status !== "RESOLVED" && (
          <button className="button secondary" disabled={busyEventId === event.id} onClick={handleDefer}>
            {busyEventId === event.id ? "處理中…" : "延後追蹤"}
          </button>
        )}
        {(event.status === "ACKNOWLEDGED" || event.status === "DEFERRED") && (
          <button className="button resolve" disabled={busyEventId === event.id} onClick={handleResolve}>
            {busyEventId === event.id ? "處理中…" : "標示為已處理"}
          </button>
        )}
      </div>
    </article>
  );
}
