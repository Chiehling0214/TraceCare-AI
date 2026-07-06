import { apiPost } from "./client";
import type { DemoActionResponse, ImportCommitResponse, ImportPreviewResponse } from "../types/imports";

interface ImportPayload {
  source_filename: string;
  content: string;
}

export const previewLabImport = (payload: ImportPayload) =>
  apiPost<ImportPreviewResponse>("/import/labs/preview", payload);

export const commitLabImport = (payload: ImportPayload) =>
  apiPost<ImportCommitResponse>("/import/labs/commit", payload);

export const previewDocumentImport = (payload: ImportPayload) =>
  apiPost<ImportPreviewResponse>("/import/documents/preview", payload);

export const commitDocumentImport = (payload: ImportPayload) =>
  apiPost<ImportCommitResponse>("/import/documents/commit", payload);

export const resetDemo = () => apiPost<DemoActionResponse>("/development/reset-demo");
export const seedDemo = () => apiPost<DemoActionResponse>("/development/seed-demo");
export const runDemoAnalysis = () => apiPost<DemoActionResponse>("/development/run-demo-analysis");
