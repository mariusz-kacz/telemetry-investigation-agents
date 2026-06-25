import type {
  DemoCaseId,
  Investigation,
  InvestigationRunSummaryResponse
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...init?.headers
    },
    ...init
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }

  return response.json() as Promise<T>;
}

export function listDemoCases(): Promise<DemoCaseId[]> {
  return request<DemoCaseId[]>("/api/v1/demo-cases");
}

export function startInvestigation(caseId: DemoCaseId): Promise<Investigation> {
  return request<Investigation>("/api/v1/investigations", {
    method: "POST",
    body: JSON.stringify({ case_id: caseId })
  });
}

export function listInvestigationRuns(): Promise<InvestigationRunSummaryResponse> {
  return request<InvestigationRunSummaryResponse>("/api/v1/investigations");
}

export function getInvestigation(runId: string): Promise<Investigation> {
  return request<Investigation>(`/api/v1/investigations/${runId}`);
}

export function submitHumanReview(
  runId: string,
  approved: boolean
): Promise<Investigation> {
  return request<Investigation>(`/api/v1/investigations/${runId}/review`, {
    method: "POST",
    body: JSON.stringify({ approved })
  });
}
