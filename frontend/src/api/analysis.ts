import { apiPost } from "./client";
import type { AnalysisRunResponse, ContradictionAnalysisRunResponse } from "../types/event";

export const runPrototypeAnalysis = () => apiPost<AnalysisRunResponse>("/prototype/run-analysis");

export const runContradictionAnalysis = () =>
  apiPost<ContradictionAnalysisRunResponse>("/prototype/run-contradiction-analysis");
