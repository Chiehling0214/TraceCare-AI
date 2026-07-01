import { formatDateTime } from "../format";
import type { ClinicalDocument, ClinicalFact } from "../types/document";
import { EmptyState } from "./States";

interface Props {
  facts: ClinicalFact[];
  documents: ClinicalDocument[];
}

export function ClinicalFactsPanel({ facts, documents }: Props) {
  if (!facts.length) return <EmptyState label="目前沒有結構化臨床事實。" />;

  const documentById = new Map(documents.map((document) => [document.id, document]));

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>事實類型</th>
            <th>主體</th>
            <th>極性</th>
            <th>狀態</th>
            <th>來源位置</th>
            <th>觀察時間</th>
            <th>來源文件</th>
          </tr>
        </thead>
        <tbody>
          {facts.map((fact) => {
            const document = documentById.get(fact.document_id);
            return (
              <tr key={fact.id}>
                <td>{fact.fact_type}</td>
                <td>{fact.subject}</td>
                <td>
                  <span className={`badge polarity-${fact.polarity}`}>{fact.polarity}</span>
                </td>
                <td>{fact.status}</td>
                <td>
                  {fact.source_section} L{fact.source_line}:{fact.source_start_char}-{fact.source_end_char}
                </td>
                <td>{formatDateTime(fact.observed_at)}</td>
                <td className="source">{document?.source_document ?? `document:${fact.document_id}`}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
