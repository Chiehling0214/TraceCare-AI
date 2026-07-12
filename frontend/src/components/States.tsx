export function LoadingState({ label }: { label: string }) {
  return <div className="state-box">{label}</div>;
}

export function EmptyState({ label }: { label: string }) {
  return <div className="state-box empty">{label}</div>;
}

export function ErrorState({ label, onRetry }: { label: string; onRetry?: () => void }) {
  return (
    <div className="state-box error">
      <div>{label}</div>
      {onRetry && (
        <button className="button secondary" onClick={onRetry}>
          重試
        </button>
      )}
    </div>
  );
}

export function OfflineBanner({ detail }: { detail?: string | null }) {
  return (
    <div className="message warning">
      後端目前無法連線。請確認 Docker Compose 或 FastAPI 服務正在執行。
      {detail ? <span> {detail}</span> : null}
    </div>
  );
}
