import { apiPost } from "./client";
import type { AnalysisRunResponse, ContradictionAnalysisRunResponse, RiskEvaluationResponse } from "../types/event";

export const runPrototypeAnalysis = () => apiPost<AnalysisRunResponse>("/prototype/run-analysis");

export const runContradictionAnalysis = () =>
  apiPost<ContradictionAnalysisRunResponse>("/prototype/run-contradiction-analysis");

export const runRiskEvaluation = () => apiPost<RiskEvaluationResponse>("/prototype/run-risk-evaluation");
