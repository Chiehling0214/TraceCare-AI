export function LoadingState({ label }: { label: string }) {
  return <div className="state-box">{label}</div>;
}

export function EmptyState({ label }: { label: string }) {
  return <div className="state-box empty">{label}</div>;
}

export function ErrorState({ label }: { label: string }) {
  return <div className="state-box error">{label}</div>;
}
