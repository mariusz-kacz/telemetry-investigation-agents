export type DemoCaseId = string;

export type Incident = {
  id: string;
  title: string;
  service: string;
  impact: string;
};

export type Hypothesis = {
  id: string;
  summary: string;
  confidence: number;
  status: string;
  evidence_ids: string[];
};

export type TopHypothesis = {
  id: string;
  statement: string;
  category: string;
  confidence: number;
  review_status: string;
  evidence_ids: string[];
};

export type Evidence = {
  evidence_id: string;
  source: string;
  summary: string;
  citation: string;
  strength: string;
};

export type ReportCitation = {
  evidence_id: string;
  source: string;
  summary: string;
  citation: string;
};

export type FinalReport = {
  incident_id: string;
  summary: string;
  confidence: number;
  uncertainty: string | null;
  selected_hypothesis_id: string | null;
  category: string | null;
  human_review_status: string;
  evidence_citations: ReportCitation[];
};

export type InvestigationRunSummary = {
  run_id: string;
  case_id: string;
  demo_provider: string;
  incident_id: string;
  status: string;
};

export type InvestigationRunSummaryResponse = {
  runs: InvestigationRunSummary[];
};

export type Investigation = {
  run_id: string;
  case_id: string;
  demo_provider: string;
  status: string;
  incident: Incident;
  top_hypothesis: TopHypothesis | null;
  hypotheses: Hypothesis[];
  evidence: Evidence[];
  human_review_required: boolean;
  review_reasons: string[];
  warnings: string[];
  report_ready: boolean;
  final_report: FinalReport | null;
};
