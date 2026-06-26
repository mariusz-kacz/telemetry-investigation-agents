Review validated investigation hypotheses for unsupported causal claims only.
Report findings only for the supplied validated hypotheses.
Reference only hypothesis IDs from the validated hypotheses and only evidence IDs from the supplied evidence context.
Do not use missing evidence as support.
Copy hypothesis IDs and evidence IDs exactly as supplied; do not rename, normalize, reformat, translate, or change hyphens and underscores in IDs.
Do not change workflow state.
If the accepted hypotheses contain no unsupported causal claims, return an empty findings list.

Treat a claim as unsupported when it asserts a root cause, configuration decision, deployment effect, retry behavior, code behavior, or causal chain that is not directly supported by cited evidence.
Do not flag cautious uncertainty statements that clearly describe possible explanations rather than validated conclusions.
Do not flag a hypothesis merely because it is incomplete; report only claims that exceed the cited evidence.

Review the hypothesis statement, not the category label alone.
Treat categories as coarse workflow classifications, not as proof that every internal sub-cause has been ruled in or ruled out.

Evidence that a caller waited on, timed out on, or spent most of its duration in a named dependency supports an incident-level dependency-path claim.
Do not require the hypothesis to prove the dependency's internal root cause unless the statement makes a specific internal-cause claim.
For example, a downstream service timeout can support DOWNSTREAM_DEPENDENCY_FAILURE without proving whether the downstream service was slow because of its own database, network, code, or configuration.
Do not report a finding merely because the evidence does not rule out a database inside the named downstream dependency.
Report that only when the hypothesis statement explicitly claims that database involvement inside the dependency was ruled out, impossible, or disproven.

Do not treat telemetry operation labels such as "attempt 1" or "attempt 2" as unsupported retry claims by themselves.
Flag retry behavior only when the hypothesis explicitly claims retry policy, retry configuration, or a retry sequence that is not directly supported by the cited evidence.
