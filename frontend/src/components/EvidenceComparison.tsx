import { formatDateTime } from "../format";
import type { EventDetail } from "../types/event";

export function EvidenceComparison({ detail }: { detail: EventDetail }) {
  const previous = detail.evidence.find((item) => item.relation_type === "PREVIOUS_VALUE");
  const current = detail.evidence.find((item) => item.relation_type === "CURRENT_VALUE");
  if (!previous || !current) {
    return <p className="muted">此事件沒有完整的前後值 evidence。</p>;
  }
  return (
    <div className="evidence-grid">
      <EvidenceColumn title="前次值" relation={previous.relation_type} item={previous.lab_result} />
      <EvidenceColumn title="目前值" relation={current.relation_type} item={current.lab_result} />
    </div>
  );
}

function EvidenceColumn({
  title,
  relation,
  item
}: {
  title: string;
  relation: string;
  item: EventDetail["evidence"][number]["lab_result"];
}) {
  return (
    <div className="evidence-card">
      <span className="relation">{relation}</span>
      <h4>{title}</h4>
      <p className="evidence-value">
        {item.value} {item.unit}
      </p>
      <p>{formatDateTime(item.observed_at)}</p>
      <p className="source">{item.source_document}</p>
    </div>
  );
}
