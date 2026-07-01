import { useEffect, useMemo, useState } from "react";

import { runPrototypeAnalysis } from "../api/analysis";
import { fetchDeviceState } from "../api/device";
import { fetchPatients } from "../api/patients";
import { DeviceStateCard } from "../components/DeviceStateCard";
import { EmptyState, ErrorState, LoadingState } from "../components/States";
import { PatientTable } from "../components/PatientTable";
import type { DeviceState } from "../types/device";
import type { PatientSummary } from "../types/patient";

export function PatientOverviewPage() {
  const [patients, setPatients] = useState<PatientSummary[]>([]);
  const [device, setDevice] = useState<DeviceState | null>(null);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function load() {
    setError(null);
    const [patientsPayload, devicePayload] = await Promise.all([fetchPatients(), fetchDeviceState()]);
    setPatients(patientsPayload.items);
    setDevice(devicePayload);
  }

  useEffect(() => {
    load()
      .catch(() => setError("資料載入失敗，請稍後再試。"))
      .finally(() => setLoading(false));
  }, []);

  const stats = useMemo(
    () => ({
      total: patients.length,
      review: patients.filter((patient) => patient.current_severity !== "NORMAL").length,
      openEvents: patients.reduce((sum, patient) => sum + patient.open_event_count, 0)
    }),
    [patients]
  );

  async function handleRunAnalysis() {
    setRunning(true);
    setMessage(null);
    setError(null);
    try {
      const result = await runPrototypeAnalysis();
      await load();
      setMessage(`原型分析已完成。新增 ${result.events_created} 筆事件，略過重複 ${result.events_skipped_as_duplicates} 筆。`);
    } catch {
      setError("分析執行失敗，請檢查後端服務。");
    } finally {
      setRunning(false);
    }
  }

  if (loading) return <LoadingState label="正在載入病人資料…" />;
  if (error && patients.length === 0) return <ErrorState label={error} />;

  return (
    <main>
      <div className="page-heading">
        <div>
          <h2>病人總覽</h2>
          <p>依目前風險狀態與未處理事件排序</p>
        </div>
        <button className="button" disabled={running} onClick={handleRunAnalysis}>
          {running ? "分析中…" : "執行原型分析"}
        </button>
      </div>
      {message && <div className="message success">{message}</div>}
      {error && <div className="message error">{error}</div>}
      <section className="summary-grid">
        <StatCard label="合成病人" value={stats.total.toString()} />
        <StatCard label="待確認病人" value={stats.review.toString()} />
        <StatCard label="未處理事件" value={stats.openEvents.toString()} />
        <StatCard label="設備狀態" value={device?.state ?? "LOADING"} />
      </section>
      <DeviceStateCard device={device} />
      <section className="panel">
        <div className="section-title">
          <h2>合成病人清單</h2>
        </div>
        {patients.length ? <PatientTable patients={patients} /> : <EmptyState label="目前沒有病人資料。" />}
      </section>
    </main>
  );
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="stat-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
