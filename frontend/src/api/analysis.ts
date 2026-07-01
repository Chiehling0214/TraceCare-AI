import { apiPost } from "./client";
import type { AnalysisRunResponse } from "../types/event";

export const runPrototypeAnalysis = () => apiPost<AnalysisRunResponse>("/prototype/run-analysis");
