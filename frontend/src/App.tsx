import {
  AlertTriangle,
  CheckCircle2,
  ClipboardCheck,
  Database,
  FileText,
  Gauge,
  GitBranch,
  History,
  Play,
  RefreshCcw,
  ShieldAlert,
  Sparkles
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import {
  getInvestigation,
  listInvestigationRuns,
  listDemoCases,
  startInvestigation,
  submitHumanReview
} from "./api";
import type {
  DemoCaseId,
  Evidence,
  Hypothesis,
  Investigation,
  InvestigationRunSummary
} from "./types";

const fallbackCases = [
  "checkout-database-timeout",
  "downstream-dependency-latency",
  "conflicting-evidence",
  "insufficient-evidence"
];

function formatLabel(value: string): string {
  return value
    .replaceAll("-", " ")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function confidencePercent(value: number): number {
  return Math.round(value * 100);
}

function statusTone(status: string): string {
  if (status === "accepted" || status === "completed") {
    return "success";
  }
  if (status.includes("review") || status === "disputed") {
    return "warning";
  }
  if (status === "blocked" || status === "failed" || status === "rejected") {
    return "danger";
  }
  return "neutral";
}

function providerLabel(provider: string): string {
  if (provider === "fake") {
    return "Local Deterministic";
  }
  if (provider === "azure") {
    return "Azure OpenAI";
  }
  return formatLabel(provider);
}

function App() {
  const [cases, setCases] = useState<DemoCaseId[]>(fallbackCases);
  const [selectedCase, setSelectedCase] = useState<DemoCaseId>(fallbackCases[0]);
  const [investigation, setInvestigation] = useState<Investigation | null>(null);
  const [runHistory, setRunHistory] = useState<InvestigationRunSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingRunId, setLoadingRunId] = useState<string | null>(null);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listDemoCases()
      .then((loadedCases) => {
        if (loadedCases.length > 0) {
          setCases(loadedCases);
          setSelectedCase((current) =>
            loadedCases.includes(current) ? current : loadedCases[0]
          );
        }
      })
      .catch(() => {
        setError("Using built-in demo cases. Start FastAPI to load live cases.");
      });
    void refreshRunHistory({ showLoading: false });
  }, []);

  const selectedCaseTitle = useMemo(
    () => formatLabel(selectedCase),
    [selectedCase]
  );

  async function runInvestigation() {
    setLoading(true);
    setError(null);
    try {
      const result = await startInvestigation(selectedCase);
      setInvestigation(result);
      await refreshRunHistory({ showLoading: false });
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Investigation failed.");
    } finally {
      setLoading(false);
    }
  }

  async function refreshRunHistory({
    showLoading = true
  }: {
    showLoading?: boolean;
  } = {}) {
    if (showLoading) {
      setLoadingHistory(true);
    }

    try {
      const history = await listInvestigationRuns();
      setRunHistory(history.runs);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Run history failed to load.");
    } finally {
      setLoadingHistory(false);
    }
  }

  async function loadInvestigation(runId: string) {
    setLoadingRunId(runId);
    setError(null);
    try {
      const result = await getInvestigation(runId);
      setInvestigation(result);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Investigation failed to load.");
    } finally {
      setLoadingRunId(null);
    }
  }

  async function review(approved: boolean) {
    if (!investigation) {
      return;
    }

    setReviewing(true);
    setError(null);
    try {
      const result = await submitHumanReview(investigation.run_id, approved);
      setInvestigation(result);
      await refreshRunHistory({ showLoading: false });
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Review submission failed.");
    } finally {
      setReviewing(false);
    }
  }

  const topConfidence = investigation?.top_hypothesis
    ? confidencePercent(investigation.top_hypothesis.confidence)
    : 0;

  return (
    <main className="app-shell">
      <aside className="side-panel" aria-label="Demo controls">
        <div className="brand-block">
          <span className="brand-mark">
            <GitBranch size={22} aria-hidden="true" />
          </span>
          <div>
            <p className="eyebrow">LangGraph portfolio demo</p>
            <h1>Telemetry Investigation Agents</h1>
          </div>
        </div>

        <section className="control-section">
          <label htmlFor="case-select">Demo case</label>
          <select
            id="case-select"
            value={selectedCase}
            onChange={(event) => setSelectedCase(event.target.value)}
          >
            {cases.map((caseId) => (
              <option key={caseId} value={caseId}>
                {formatLabel(caseId)}
              </option>
            ))}
          </select>
          <button
            className="primary-action"
            type="button"
            onClick={runInvestigation}
            disabled={loading}
            title="Run selected investigation"
          >
            {loading ? <RefreshCcw size={18} /> : <Play size={18} />}
            {loading ? "Running" : "Run Investigation"}
          </button>
        </section>

        <RunHistoryPanel
          runs={runHistory}
          activeRunId={investigation?.run_id}
          loading={loadingHistory}
          loadingRunId={loadingRunId}
          onRefresh={() => void refreshRunHistory()}
          onSelectRun={(runId) => void loadInvestigation(runId)}
        />

        <section className="workflow-card" aria-label="Workflow stages">
          <h2>Workflow</h2>
          <ol>
            <li>
              <Database size={16} aria-hidden="true" />
              Retrieve evidence
            </li>
            <li>
              <Sparkles size={16} aria-hidden="true" />
              Generate hypotheses
            </li>
            <li>
              <ShieldAlert size={16} aria-hidden="true" />
              Validate and critique
            </li>
            <li>
              <ClipboardCheck size={16} aria-hidden="true" />
              Human gate
            </li>
          </ol>
        </section>
      </aside>

      <section className="dashboard">
        <header className="dashboard-header">
          <div>
            <p className="eyebrow">Selected incident</p>
            <h2>{investigation?.incident.title ?? selectedCaseTitle}</h2>
            <p className="subtle">
              {investigation
                ? `${investigation.incident.service} - ${formatLabel(
                    investigation.incident.impact
                  )} impact`
                : "Run the workflow to inspect hypotheses, citations, and review gates."}
            </p>
          </div>
          <div className="header-badges">
            <StatusBadge
              label={investigation?.status ?? "ready"}
              tone={statusTone(investigation?.status ?? "ready")}
            />
            {investigation ? (
              <StatusBadge
                label={providerLabel(investigation.demo_provider)}
                tone="neutral"
              />
            ) : null}
          </div>
        </header>

        {error ? (
          <div className="notice warning-notice" role="status">
            <AlertTriangle size={18} aria-hidden="true" />
            <span>{error}</span>
          </div>
        ) : null}

        <section className="metrics-grid" aria-label="Investigation summary">
          <MetricTile
            icon={<Gauge size={22} aria-hidden="true" />}
            label="Top confidence"
            value={investigation?.top_hypothesis ? `${topConfidence}%` : "--"}
            meterValue={topConfidence}
          />
          <MetricTile
            icon={<FileText size={22} aria-hidden="true" />}
            label="Evidence items"
            value={String(investigation?.evidence.length ?? 0)}
          />
          <MetricTile
            icon={<ShieldAlert size={22} aria-hidden="true" />}
            label="Human review"
            value={
              investigation?.human_review_required
                ? "Required"
                : investigation
                  ? "Bypassed"
                  : "Pending"
            }
          />
        </section>

        <section className="content-grid">
          <TopHypothesisPanel investigation={investigation} />
          <FinalReportPanel investigation={investigation} />
          <EvidencePanel evidence={investigation?.evidence ?? []} />
          <HypothesisPanel hypotheses={investigation?.hypotheses ?? []} />
          <ReviewPanel
            investigation={investigation}
            reviewing={reviewing}
            onReview={review}
          />
        </section>
      </section>
    </main>
  );
}

function StatusBadge({ label, tone }: { label: string; tone: string }) {
  return <span className={`status-badge ${tone}`}>{formatLabel(label)}</span>;
}

function MetricTile({
  icon,
  label,
  value,
  meterValue
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  meterValue?: number;
}) {
  return (
    <article className="metric-tile">
      <div className="metric-icon">{icon}</div>
      <div>
        <p>{label}</p>
        <strong>{value}</strong>
      </div>
      {meterValue !== undefined ? (
        <div className="meter" aria-hidden="true">
          <span style={{ width: `${meterValue}%` }} />
        </div>
      ) : null}
    </article>
  );
}

function RunHistoryPanel({
  runs,
  activeRunId,
  loading,
  loadingRunId,
  onRefresh,
  onSelectRun
}: {
  runs: InvestigationRunSummary[];
  activeRunId?: string;
  loading: boolean;
  loadingRunId: string | null;
  onRefresh: () => void;
  onSelectRun: (runId: string) => void;
}) {
  return (
    <section className="history-panel" aria-label="Past investigation runs">
      <div className="history-heading">
        <div>
          <h2>Past Runs</h2>
          <p>
            {runs.length === 1
              ? "1 investigation"
              : `${runs.length} investigations`}
          </p>
        </div>
        <button
          type="button"
          className="icon-action"
          onClick={onRefresh}
          disabled={loading}
          title="Refresh run history"
          aria-label="Refresh run history"
        >
          <RefreshCcw size={16} aria-hidden="true" />
        </button>
      </div>

      {runs.length === 0 ? (
        <p className="history-empty">Completed and review-pending runs appear here.</p>
      ) : (
        <div className="run-list">
          {runs.map((run) => {
            const isActive = run.run_id === activeRunId;
            const isLoading = run.run_id === loadingRunId;

            return (
              <button
                key={run.run_id}
                type="button"
                className={`run-item ${isActive ? "active" : ""}`}
                onClick={() => onSelectRun(run.run_id)}
                disabled={isLoading}
                title={`Load ${formatLabel(run.case_id)}`}
              >
                <span className="run-icon">
                  {isLoading ? (
                    <RefreshCcw size={16} aria-hidden="true" />
                  ) : (
                    <History size={16} aria-hidden="true" />
                  )}
                </span>
                <span className="run-main">
                  <strong>{formatLabel(run.case_id)}</strong>
                  <small>
                    {providerLabel(run.demo_provider)} - {run.incident_id}
                  </small>
                </span>
                <StatusBadge label={run.status} tone={statusTone(run.status)} />
              </button>
            );
          })}
        </div>
      )}
    </section>
  );
}

function FinalReportPanel({
  investigation
}: {
  investigation: Investigation | null;
}) {
  const report = investigation?.final_report;

  return (
    <article className="panel report-panel">
      <div className="panel-heading">
        <h3>Final Report</h3>
        {report ? (
          <StatusBadge
            label={report.human_review_status}
            tone={statusTone(report.human_review_status)}
          />
        ) : null}
      </div>
      {report ? (
        <>
          <p className="report-summary">{report.summary}</p>
          <div className="report-facts">
            <div className="detail-row">
              <span>Confidence</span>
              <strong>{confidencePercent(report.confidence)}%</strong>
            </div>
            <div className="detail-row">
              <span>Category</span>
              <strong>{report.category ? formatLabel(report.category) : "None"}</strong>
            </div>
            <div className="detail-row">
              <span>Selected hypothesis</span>
              <strong>{report.selected_hypothesis_id ?? "None"}</strong>
            </div>
          </div>
          {report.uncertainty ? (
            <p className="report-uncertainty">{report.uncertainty}</p>
          ) : null}
          <div className="report-citations" aria-label="Report citations">
            {report.evidence_citations.map((citation) => (
              <code key={citation.evidence_id}>
                {citation.evidence_id} - {citation.citation}
              </code>
            ))}
          </div>
        </>
      ) : (
        <EmptyState text="The final report appears after the workflow is approved or safely bypasses human review." />
      )}
    </article>
  );
}

function TopHypothesisPanel({
  investigation
}: {
  investigation: Investigation | null;
}) {
  const topHypothesis = investigation?.top_hypothesis;

  return (
    <article className="panel top-panel">
      <div className="panel-heading">
        <h3>Top Hypothesis</h3>
        {topHypothesis ? (
          <StatusBadge
            label={topHypothesis.review_status}
            tone={statusTone(topHypothesis.review_status)}
          />
        ) : null}
      </div>
      {topHypothesis ? (
        <>
          <p className="statement">{topHypothesis.statement}</p>
          <div className="detail-row">
            <span>Category</span>
            <strong>{formatLabel(topHypothesis.category)}</strong>
          </div>
          <div className="detail-row">
            <span>Confidence</span>
            <strong>{confidencePercent(topHypothesis.confidence)}%</strong>
          </div>
          <div className="evidence-strip">
            {topHypothesis.evidence_ids.map((evidenceId) => (
              <span key={evidenceId}>{evidenceId}</span>
            ))}
          </div>
        </>
      ) : (
        <EmptyState text="No hypothesis yet. Start an investigation to populate this panel." />
      )}
    </article>
  );
}

function EvidencePanel({ evidence }: { evidence: Evidence[] }) {
  return (
    <article className="panel evidence-panel">
      <div className="panel-heading">
        <h3>Evidence Citations</h3>
        <span className="count-pill">{evidence.length}</span>
      </div>
      {evidence.length === 0 ? (
        <EmptyState text="Retrieved log, trace, and metric citations will appear here." />
      ) : (
        <div className="evidence-list">
          {evidence.map((item) => (
            <div className="evidence-item" key={item.evidence_id}>
              <div>
                <span className="source-pill">{formatLabel(item.source)}</span>
                <span className={`strength-pill ${item.strength}`}>
                  {formatLabel(item.strength)}
                </span>
              </div>
              <p>{item.summary}</p>
              <code>{item.citation}</code>
            </div>
          ))}
        </div>
      )}
    </article>
  );
}

function HypothesisPanel({ hypotheses }: { hypotheses: Hypothesis[] }) {
  return (
    <article className="panel hypothesis-panel">
      <div className="panel-heading">
        <h3>Hypothesis Review</h3>
        <span className="count-pill">{hypotheses.length}</span>
      </div>
      {hypotheses.length === 0 ? (
        <EmptyState text="Validated and critic-reviewed hypotheses will appear here." />
      ) : (
        <div className="hypothesis-list">
          {hypotheses.map((hypothesis) => (
            <div className="hypothesis-item" key={hypothesis.id}>
              <div className="hypothesis-title">
                <StatusBadge
                  label={hypothesis.status}
                  tone={statusTone(hypothesis.status)}
                />
                <strong>{confidencePercent(hypothesis.confidence)}%</strong>
              </div>
              <p>{hypothesis.summary}</p>
            </div>
          ))}
        </div>
      )}
    </article>
  );
}

function ReviewPanel({
  investigation,
  reviewing,
  onReview
}: {
  investigation: Investigation | null;
  reviewing: boolean;
  onReview: (approved: boolean) => void;
}) {
  const reviewRequired = investigation?.human_review_required ?? false;
  const reviewActionAvailable =
    reviewRequired && investigation?.status === "awaiting_review";

  return (
    <article className="panel review-panel">
      <div className="panel-heading">
        <h3>Human Review Gate</h3>
        {reviewActionAvailable ? (
          <StatusBadge label="required" tone="warning" />
        ) : reviewRequired ? (
          <StatusBadge
            label="decided"
            tone={statusTone(investigation?.status ?? "")}
          />
        ) : (
          <StatusBadge label="not required" tone="success" />
        )}
      </div>
      {investigation ? (
        <>
          <ul className="reason-list">
            {reviewDecisionMessages(investigation, reviewActionAvailable).map((reason) => (
              <li key={reason}>
                <CheckCircle2 size={16} aria-hidden="true" />
                {reason}
              </li>
            ))}
          </ul>
          <div className="review-actions">
            <button
              type="button"
              onClick={() => onReview(true)}
              disabled={!reviewActionAvailable || reviewing}
              title="Approve reviewed investigation"
            >
              <CheckCircle2 size={17} aria-hidden="true" />
              Approve
            </button>
            <button
              type="button"
              className="secondary-danger"
              onClick={() => onReview(false)}
              disabled={!reviewActionAvailable || reviewing}
              title="Reject reviewed investigation"
            >
              <AlertTriangle size={17} aria-hidden="true" />
              Reject
            </button>
          </div>
        </>
      ) : (
        <EmptyState text="Review controls activate when the workflow requires human judgment." />
      )}
    </article>
  );
}

function reviewDecisionMessages(
  investigation: Investigation,
  reviewActionAvailable: boolean
): string[] {
  if (!investigation.human_review_required) {
    return ["No review trigger was raised by the deterministic policy."];
  }

  if (!reviewActionAvailable) {
    return [
      `Review decision already submitted. Current status: ${formatLabel(
        investigation.status
      )}.`
    ];
  }

  return investigation.review_reasons.length > 0
    ? investigation.review_reasons
    : ["Human review is required before the report can be finalized."];
}

function EmptyState({ text }: { text: string }) {
  return <p className="empty-state">{text}</p>;
}

export default App;
