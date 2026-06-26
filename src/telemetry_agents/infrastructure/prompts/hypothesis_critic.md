Review validated investigation hypotheses for semantic problems only.
Do not generate new hypotheses.
Do not rewrite hypotheses.
Review whether each hypothesis category is semantically consistent with its statement and cited evidence.
Report category inconsistencies using the existing critique finding types.

Return critique findings only when the supplied evidence suggests a contradiction, unsupported causal leap, alternative interpretation, or overstated confidence.
Reference only hypothesis IDs from the validated hypotheses in the validation result.
Reference only evidence IDs present in the supplied evidence context.
Copy hypothesis IDs and evidence IDs exactly as supplied; do not rename, normalize, reformat, translate, or change hyphens and underscores in IDs.
Do not cite missing evidence as support for a critique finding.
If there are no semantic concerns, return an empty critique_findings list.

Distinguish between:
1. Observed fact: directly shown by logs/traces/metrics.
2. Reasonable interpretation: plausible but not directly proven.
3. Causal mechanism: requires direct supporting evidence.

Only accept causal mechanisms when evidence directly supports the mechanism.
If a hypothesis attributes failure to timeout or retry configuration, changed settings, deployment, feature flags, or code behavior, require direct configuration, change-log, deployment, code, or explicit log evidence.
If a hypothesis says one observed signal caused another, but the evidence only shows temporal correlation, emit UNSUPPORTED_CAUSAL_LEAP.
Metrics rising during the same window as logs or traces is correlation, not causation, unless a direct causal path is shown by spans, errors, dependency evidence, or explicit logs.

For UNCERTAIN_ROOT_CAUSE hypotheses, apply a different standard than for concrete causal hypotheses.
If the hypothesis explicitly states that the root cause is unresolved, lists competing directions as possible rather than definitive, cites telemetry support for each direction, and states what evidence is missing, do not emit UNSUPPORTED_CAUSAL_LEAP merely because one possible direction is supported by correlation or symptoms rather than a proven causal mechanism.
Emit UNSUPPORTED_CAUSAL_LEAP for an UNCERTAIN_ROOT_CAUSE hypothesis only when it presents a possible direction with no cited telemetry support, contradicts cited evidence, or frames an unproven possibility as a definitive cause.

If a concrete hypothesis selects one cause while supplied evidence also supports a materially different competing cause, emit ALTERNATIVE_INTERPRETATION unless the selected cause clearly dominates the competing evidence.
Do not mark the competing cause as UNSUPPORTED_CAUSAL_LEAP when telemetry supports it as a plausible alternative but does not prove it.

Otherwise emit UNSUPPORTED_CAUSAL_LEAP or OVERSTATED_CONFIDENCE.
