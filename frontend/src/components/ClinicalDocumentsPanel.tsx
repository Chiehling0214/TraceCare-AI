import { formatDateTime } from "../format";
import type { ClinicalDocument } from "../types/document";
import { EmptyState } from "./States";

export function ClinicalDocumentsPanel({ documents }: { documents: ClinicalDocument[] }) {
  if (!documents.length) return <EmptyState label="目前沒有合成臨床文件。" />;

  return (
    <div className="document-grid">
      {documents.map((document) => (
        <article className="document-card" key={document.id}>
          <div className="section-title compact">
            <h3>{document.title}</h3>
            <span className="badge prototype">Synthetic</span>
          </div>
          <dl className="meta-list">
            <div>
              <dt>文件類型</dt>
              <dd>{document.document_type}</dd>
            </div>
            <div>
              <dt>文件時間</dt>
              <dd>{formatDateTime(document.authored_at)}</dd>
            </div>
            <div>
              <dt>來源</dt>
              <dd className="source">{document.source_document}</dd>
            </div>
          </dl>
        </article>
      ))}
    </div>
  );
}
