import { useState } from "react";

import { ApiRequestError } from "../api/client";
import {
  commitDocumentImport,
  commitLabImport,
  previewDocumentImport,
  previewLabImport,
  resetDemo,
  runDemoAnalysis,
  seedDemo
} from "../api/imports";
import { formatDateTime } from "../format";
import { OfflineBanner } from "../components/States";
import type { DemoActionResponse, ImportCommitResponse, ImportPreviewResponse } from "../types/imports";

const LAB_EXAMPLE = `patient_code,display_name,test_name,value,unit,reference_min,reference_max,observed_at,source_document
P020,Synthetic Import Patient 20,creatinine,0.8,mg/dL,0.6,1.2,2026-06-24T08:00:00Z,import_labs_20260624.csv
P020,Synthetic Import Patient 20,creatinine,1.4,mg/dL,0.6,1.2,2026-06-25T08:00:00Z,import_labs_20260625.csv`;

const DOCUMENT_EXAMPLE = `{
  "schema_version": "tracecare-documents-json-v1",
  "documents": [
    {
      "patient_code": "P020",
      "display_name": "Synthetic Import Patient 20",
      "document_type": "ADMISSION_NOTE",
      "title": "Synthetic import admission note",
      "source_document": "import_note_p020_20260625.txt",
      "authored_at": "2026-06-25T09:00:00Z",
      "facts": [
        {
          "fact_type": "ALLERGY_STATEMENT",
          "subject": "penicillin",
          "polarity": "PRESENT",
          "value": "Allergy: Penicillin",
          "status": "ACTIVE",
          "source_section": "Allergies",
          "source_line": 4,
          "source_start_char": 10,
          "source_end_char": 20,
          "observed_at": "2026-06-25T09:00:00Z"
        }
      ]
    }
  ]
}`;

type ImportKind = "labs" | "documents";

export function DemoDataPage() {
  const [labFilename, setLabFilename] = useState("demo_labs.csv");
  const [labContent, setLabContent] = useState(LAB_EXAMPLE);
  const [documentFilename, setDocumentFilename] = useState("demo_documents.json");
  const [documentContent, setDocumentContent] = useState(DOCUMENT_EXAMPLE);
  const [labResult, setLabResult] = useState<ImportPreviewResponse | ImportCommitResponse | null>(null);
  const [documentResult, setDocumentResult] = useState<ImportPreviewResponse | ImportCommitResponse | null>(null);
  const [demoResult, setDemoResult] = useState<DemoActionResponse | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [offline, setOffline] = useState(false);

  async function runImportAction(kind: ImportKind, action: "preview" | "commit") {
    setBusy(`${kind}-${action}`);
    setError(null);
    setOffline(false);
    try {
      if (kind === "labs") {
        const payload = { source_filename: labFilename, content: labContent };
        setLabResult(action === "preview" ? await previewLabImport(payload) : await commitLabImport(payload));
      } else {
        const payload = { source_filename: documentFilename, content: documentContent };
        setDocumentResult(
          action === "preview" ? await previewDocumentImport(payload) : await commitDocumentImport(payload)
        );
      }
    } catch (err) {
      setOffline(err instanceof ApiRequestError && err.code === "BACKEND_UNAVAILABLE");
      setError(err instanceof Error ? err.message : "Import action failed.");
    } finally {
      setBusy(null);
    }
  }

  async function runDemoAction(action: "reset" | "seed" | "run") {
    setBusy(`demo-${action}`);
    setError(null);
    setOffline(false);
    try {
      if (action === "reset") setDemoResult(await resetDemo());
      if (action === "seed") setDemoResult(await seedDemo());
      if (action === "run") setDemoResult(await runDemoAnalysis());
    } catch (err) {
      setOffline(err instanceof ApiRequestError && err.code === "BACKEND_UNAVAILABLE");
      setError(err instanceof Error ? err.message : "Demo action failed.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <main>
      <div className="page-heading">
        <div>
          <h2>Demo Data Management</h2>
          <p>固定 schema synthetic CSV/JSON import、reset、seed 與 run-demo workflow。</p>
        </div>
      </div>
      <div className="message warning">
        只允許 synthetic data。不要上傳或貼上真實病人資料、真實病歷或可識別資訊。
      </div>
      {offline && <OfflineBanner />}
      {error && <div className="message error">{error}</div>}
      <section className="panel">
        <div className="section-title">
          <h2>Demo Workflow</h2>
        </div>
        <div className="actions">
          <button className="button secondary" disabled={busy !== null} onClick={() => runDemoAction("reset")}>
            Reset Demo
          </button>
          <button className="button secondary" disabled={busy !== null} onClick={() => runDemoAction("seed")}>
            Seed Demo
          </button>
          <button className="button" disabled={busy !== null} onClick={() => runDemoAction("run")}>
            Run Demo Analysis
          </button>
        </div>
        {demoResult && <DemoResult result={demoResult} />}
      </section>
      <ImportPanel
        title="Lab CSV Import"
        filename={labFilename}
        content={labContent}
        result={labResult}
        busyPreview={busy === "labs-preview"}
        busyCommit={busy === "labs-commit"}
        onFilename={setLabFilename}
        onContent={setLabContent}
        onPreview={() => runImportAction("labs", "preview")}
        onCommit={() => runImportAction("labs", "commit")}
      />
      <ImportPanel
        title="Clinical Document JSON Import"
        filename={documentFilename}
        content={documentContent}
        result={documentResult}
        busyPreview={busy === "documents-preview"}
        busyCommit={busy === "documents-commit"}
        onFilename={setDocumentFilename}
        onContent={setDocumentContent}
        onPreview={() => runImportAction("documents", "preview")}
        onCommit={() => runImportAction("documents", "commit")}
      />
    </main>
  );
}

function ImportPanel({
  title,
  filename,
  content,
  result,
  busyPreview,
  busyCommit,
  onFilename,
  onContent,
  onPreview,
  onCommit
}: {
  title: string;
  filename: string;
  content: string;
  result: ImportPreviewResponse | ImportCommitResponse | null;
  busyPreview: boolean;
  busyCommit: boolean;
  onFilename: (value: string) => void;
  onContent: (value: string) => void;
  onPreview: () => void;
  onCommit: () => void;
}) {
  const committed = result && "committed" in result ? result.committed : null;
  return (
    <section className="panel import-panel">
      <div className="section-title">
        <h2>{title}</h2>
        {result && <span className={`badge ${result.valid ? "summary-GENERATED" : "summary-REJECTED"}`}>{result.valid ? "VALID" : "INVALID"}</span>}
      </div>
      <label className="field-label">
        Source filename
        <input value={filename} onChange={(event) => onFilename(event.target.value)} />
      </label>
      <label className="field-label">
        Content
        <textarea value={content} onChange={(event) => onContent(event.target.value)} rows={12} spellCheck={false} />
      </label>
      <div className="actions">
        <button className="button secondary" disabled={busyPreview || busyCommit} onClick={onPreview}>
          {busyPreview ? "Previewing..." : "Preview"}
        </button>
        <button className="button" disabled={busyPreview || busyCommit} onClick={onCommit}>
          {busyCommit ? "Committing..." : "Commit"}
        </button>
      </div>
      {committed !== null && (
        <div className={committed ? "message success" : "message error"}>
          {committed ? "Import committed." : "Import rejected; no partial data was committed."}
        </div>
      )}
      {result && <ImportResult result={result} />}
    </section>
  );
}

function ImportResult({ result }: { result: ImportPreviewResponse | ImportCommitResponse }) {
  return (
    <div className="import-result">
      <dl className="meta-grid">
        <div>
          <dt>Rows</dt>
          <dd>{result.rows_received}</dd>
        </div>
        <div>
          <dt>Valid</dt>
          <dd>{result.rows_valid}</dd>
        </div>
        <div>
          <dt>Duplicates</dt>
          <dd>{result.duplicates_detected}</dd>
        </div>
        <div>
          <dt>Schema</dt>
          <dd>{result.schema_version}</dd>
        </div>
      </dl>
      {result.errors.length > 0 && (
        <div className="message error">
          {result.errors.map((item) => (
            <div key={`${item.row}-${item.field}-${item.code}`}>
              {item.row ? `row ${item.row}: ` : ""}
              {item.field ? `${item.field}: ` : ""}
              {item.code} - {item.message}
            </div>
          ))}
        </div>
      )}
      {result.preview_rows.length > 0 && (
        <table className="data-table">
          <thead>
            <tr>
              <th>Row</th>
              <th>Action</th>
              <th>Patient</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody>
            {result.preview_rows.map((row) => (
              <tr key={`${row.row}-${row.source_position}`}>
                <td>{row.row}</td>
                <td>{row.action}</td>
                <td>{row.patient_code}</td>
                <td>{row.source_position}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

function DemoResult({ result }: { result: DemoActionResponse }) {
  return (
    <dl className="meta-grid">
      <div>
        <dt>Status</dt>
        <dd>{result.status}</dd>
      </div>
      <div>
        <dt>Patients</dt>
        <dd>{result.patients_created || result.patients_deleted}</dd>
      </div>
      <div>
        <dt>Events</dt>
        <dd>{result.events_created}</dd>
      </div>
      <div>
        <dt>Time</dt>
        <dd>{formatDateTime(result.created_at)}</dd>
      </div>
    </dl>
  );
}
