import { useEffect, useState } from "react";

import { fetchDeviceState } from "../api/device";
import { fetchPatientDocuments, fetchPatientFacts } from "../api/documents";
import { fetchEvent } from "../api/events";
import { fetchPatientEvidenceGraph } from "../api/graph";
import { fetchPatient, fetchPatientEvents, fetchPatientLabs } from "../api/patients";
import { ClinicalEventCard } from "../components/ClinicalEventCard";
import { ClinicalDocumentsPanel } from "../components/ClinicalDocumentsPanel";
import { ClinicalFactsPanel } from "../components/ClinicalFactsPanel";
import { DeviceStateCard } from "../components/DeviceStateCard";
import { EvidenceGraphPanel } from "../components/EvidenceGraphPanel";
import { LabResultsTable } from "../components/LabResultsTable";
import { EmptyState, ErrorState, LoadingState } from "../components/States";
import { PrototypeNotice } from "../components/PrototypeNotice";
import { RiskBadge } from "../components/StatusBadges";
import { SummaryPanel } from "../components/SummaryPanel";
import { formatDateTime } from "../format";
import { Link } from "../router";
import type { DeviceState } from "../types/device";
import type { ClinicalDocument, ClinicalFact } from "../types/document";
import type { ClinicalEvent, EventDetail } from "../types/event";
import type { EvidenceGraph } from "../types/graph";
import type { LabResult } from "../types/lab";
import type { PatientDetail } from "../types/patient";

export function PatientDetailPage({ patientId }: { patientId: number }) {
  const [patient, setPatient] = useState<PatientDetail | null>(null);
  const [labs, setLabs] = useState<LabResult[]>([]);
  const [documents, setDocuments] = useState<ClinicalDocument[]>([]);
  const [facts, setFacts] = useState<ClinicalFact[]>([]);
  const [events, setEvents] = useState<ClinicalEvent[]>([]);
  const [details, setDetails] = useState<Record<number, EventDetail>>({});
  const [graph, setGraph] = useState<EvidenceGraph | null>(null);
  const [device, setDevice] = useState<DeviceState | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [busyEventId, setBusyEventId] = useState<number | null>(null);

  async function load() {
    setError(null);
    const [
      patientPayload,
      labsPayload,
      eventsPayload,
      devicePayload,
      documentsPayload,
      factsPayload,
      graphPayload
    ] = await Promise.all([
      fetchPatient(patientId),
      fetchPatientLabs(patientId),
      fetchPatientEvents(patientId),
      fetchDeviceState(),
      fetchPatientDocuments(patientId),
      fetchPatientFacts(patientId),
      fetchPatientEvidenceGraph(patientId)
    ]);
    setPatient(patientPayload);
    setLabs(labsPayload.items);
    setDocuments(documentsPayload.items);
    setFacts(factsPayload.items);
    setEvents(eventsPayload.items);
    setDevice(devicePayload);
    setGraph(graphPayload);
    const eventDetails = await Promise.all(eventsPayload.items.map((event) => fetchEvent(event.id)));
    setDetails(Object.fromEntries(eventDetails.map((detail) => [detail.id, detail])));
  }

  useEffect(() => {
    load()
      .catch(() => setError("資料載入失敗，請稍後再試。"))
      .finally(() => setLoading(false));
  }, [patientId]);

  async function reloadAfterChange(feedback: string) {
    await load();
    setMessage(feedback);
  }

  if (loading) return <LoadingState label="正在載入病人詳細資料…" />;
  if (error || !patient) return <ErrorState label={error ?? "找不到指定病人。"} />;

  return (
    <main>
      <Link href="/" className="back-link">
        ← 返回病人總覽
      </Link>
      <div className="detail-layout">
        <section className="panel">
          <div className="section-title">
            <h2>{patient.patient_code}</h2>
            <RiskBadge value={patient.current_severity} />
          </div>
          <dl className="meta-grid">
            <div>
              <dt>顯示名稱</dt>
              <dd>{patient.display_name}</dd>
            </div>
            <div>
              <dt>資料型態</dt>
              <dd>Synthetic Data</dd>
            </div>
            <div>
              <dt>未處理事件</dt>
              <dd>{patient.open_event_count}</dd>
            </div>
            <div>
              <dt>最新檢驗</dt>
              <dd>{formatDateTime(patient.latest_lab_observed_at)}</dd>
            </div>
          </dl>
        </section>
        <DeviceStateCard device={device} />
      </div>
      {message && <div className="message success">{message}</div>}
      <section className="panel">
        <SummaryPanel patientId={patientId} />
      </section>
      <section className="panel">
        <div className="section-title">
          <h2>Creatinine 歷史</h2>
        </div>
        {labs.length ? <LabResultsTable labs={labs} /> : <EmptyState label="目前沒有檢驗資料。" />}
      </section>
      <section className="panel">
        <div className="section-title">
          <h2>合成臨床文件</h2>
        </div>
        <ClinicalDocumentsPanel documents={documents} />
      </section>
      <section className="panel">
        <div className="section-title">
          <h2>結構化臨床事實</h2>
        </div>
        <ClinicalFactsPanel documents={documents} facts={facts} />
      </section>
      <section className="panel">
        <div className="section-title">
          <h2>臨床事件</h2>
        </div>
        {events.length ? (
          <div className="event-list">
            {events.map((event) => (
              <ClinicalEventCard
                key={event.id}
                event={event}
                detail={details[event.id] ?? null}
                busyEventId={busyEventId}
                onDetailLoaded={(detail) => setDetails((current) => ({ ...current, [detail.id]: detail }))}
                onChanged={reloadAfterChange}
                setBusyEventId={setBusyEventId}
              />
            ))}
          </div>
        ) : (
          <EmptyState label="目前沒有臨床事件。" />
        )}
      </section>
      <section className="panel">
        <div className="section-title">
          <h2>Evidence Graph</h2>
          <span className="badge prototype">Prototype Rule</span>
        </div>
        <EvidenceGraphPanel graph={graph} />
      </section>
      <PrototypeNotice />
    </main>
  );
}
