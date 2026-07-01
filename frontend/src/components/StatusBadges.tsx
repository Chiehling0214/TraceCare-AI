const severityLabels: Record<string, string> = {
  NORMAL: "正常",
  REVIEW_REQUIRED: "待確認",
  HIGH_RISK: "高風險"
};

const statusLabels: Record<string, string> = {
  OPEN: "待處理",
  ACKNOWLEDGED: "已確認未結案",
  RESOLVED: "已處理／結案"
};

export function RiskBadge({ value }: { value: string }) {
  return <span className={`badge severity-${value}`}>{severityLabels[value] ?? value}</span>;
}

export function EventStatusBadge({ value }: { value: string }) {
  return <span className={`badge status-${value}`}>{statusLabels[value] ?? value}</span>;
}
