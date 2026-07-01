import { formatDateTime } from "../format";
import type { LabResult } from "../types/lab";

export function LabResultsTable({ labs }: { labs: LabResult[] }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>檢驗時間</th>
            <th>檢驗項目</th>
            <th>數值</th>
            <th>單位</th>
            <th>參考區間</th>
            <th>資料來源</th>
          </tr>
        </thead>
        <tbody>
          {labs.map((lab) => (
            <tr key={lab.id}>
              <td>{formatDateTime(lab.observed_at)}</td>
              <td>{lab.test_name}</td>
              <td className="value">{lab.value}</td>
              <td>{lab.unit}</td>
              <td>
                {lab.reference_min}-{lab.reference_max} {lab.unit}
              </td>
              <td className="source">{lab.source_document}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
