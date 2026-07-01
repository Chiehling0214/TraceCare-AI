import { formatDateTime } from "../format";
import { Link } from "../router";
import type { PatientSummary } from "../types/patient";
import { RiskBadge } from "./StatusBadges";

export function PatientTable({ patients }: { patients: PatientSummary[] }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>病人代碼</th>
            <th>顯示名稱</th>
            <th>風險狀態</th>
            <th>未處理事件</th>
            <th>最新檢驗時間</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {patients.map((patient) => (
            <tr key={patient.id}>
              <td className="code">{patient.patient_code}</td>
              <td>
                {patient.display_name}
                <span className="synthetic">Synthetic</span>
              </td>
              <td>
                <RiskBadge value={patient.current_severity} />
              </td>
              <td>{patient.open_event_count}</td>
              <td>{formatDateTime(patient.latest_lab_observed_at)}</td>
              <td>
                <Link className="button secondary small" href={`/patients/${patient.id}`}>
                  查看詳情
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
