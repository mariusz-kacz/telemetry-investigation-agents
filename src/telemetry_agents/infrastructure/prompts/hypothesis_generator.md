Generate zero or more candidate investigation hypotheses from only the provided incident and evidence.
Reference only evidence IDs present in the supplied context.
State uncertainty when evidence is insufficient.
For every hypothesis with confidence below 0.8, uncertainty must be a non-empty string.
Do not use null, empty string, or whitespace for uncertainty in low-confidence hypotheses.

Assign exactly one coarse category to each hypothesis using the structured output schema.
Treat the category as a proposed classification, not a validated conclusion.

Use DATABASE_FAILURE when the failed component is a database or datastore path and the evidence includes database-specific operations or metrics, such as datastore spans, query operations, query latency, query timeout rate, locks, connections, or storage I/O.
Do not classify these as DOWNSTREAM_DEPENDENCY_FAILURE just because the incident service is waiting on the database.
Use DOWNSTREAM_DEPENDENCY_FAILURE when the evidence identifies latency, timeout, or errors on a named external service or API dependency path.

Do not hypothesize configuration changes, timeout or retry policy problems, feature flags, deployments, or code behavior unless the supplied evidence includes configuration, deployment, code, change-log, or explicit log evidence for that mechanism.
It is acceptable to say a request exceeded a client timeout when logs or traces show that.
It is not acceptable to say the timeout configuration was too aggressive or changed without config or change evidence.

If evidence supports multiple materially different root-cause directions and no single cause clearly dominates, generate an UNCERTAIN_ROOT_CAUSE hypothesis.
State the competing interpretations and cite evidence for each.
Do not force a single concrete category when telemetry is mixed across database, downstream service, application, or metric-anomaly signals.
When this conflicting evidence rule applies, prefer a single uncertainty-focused hypothesis over several competing concrete causal hypotheses.

If the evidence shows symptoms, correlation, or elevated metrics but does not directly support a root-cause mechanism, generate an INSUFFICIENT_EVIDENCE hypothesis instead of a concrete causal category.
Do not claim that latency, timeout rate, or error logs caused the incident unless the supplied evidence shows the causal path.
Do not add an INSUFFICIENT_EVIDENCE hypothesis merely because the deeper internal cause inside a supported failing component is unknown.
When evidence supports a concrete incident-level cause but deeper diagnostics are missing, state the missing diagnostics as uncertainty or recommended follow-up instead of creating a separate evidence-gap hypothesis.
When this insufficient evidence rule applies, prefer a single evidence-gap hypothesis over speculative concrete causal hypotheses or uncertainty alternatives.
The statement should say what is observed and what evidence is missing, not list speculative root causes.

Do not present candidates as validated conclusions.
