import { acknowledgeEvent, fetchEvent, resolveEvent } from "../api/events";
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
          <dt>結案時間</dt>
          <dd>{formatDateTime(event.resolved_at)}</dd>
        </div>
      </dl>
      {detail?.analysis && (
        <p className="analysis-line">
          Evidence: {detail.analysis.previous_value} → {detail.analysis.current_value} {detail.analysis.unit}，
          時間差 {detail.analysis.time_difference_hours} 小時
        </p>
      )}
      {detail ? <EvidenceComparison detail={detail} /> : <button className="link-button" onClick={ensureDetail}>載入 evidence</button>}
      <div className="actions">
        {event.status === "OPEN" && (
          <button className="button" disabled={busyEventId === event.id} onClick={handleAcknowledge}>
            {busyEventId === event.id ? "處理中…" : "確認事件"}
          </button>
        )}
        {event.status === "ACKNOWLEDGED" && (
          <button className="button resolve" disabled={busyEventId === event.id} onClick={handleResolve}>
            {busyEventId === event.id ? "處理中…" : "標示為已處理"}
          </button>
        )}
      </div>
    </article>
  );
}
