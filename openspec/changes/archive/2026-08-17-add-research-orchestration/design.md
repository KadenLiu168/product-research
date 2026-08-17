## Context

See `proposal.md` for motivation. The repository currently uses one sibling module for each deterministic capability and already exposes the only durable normalized record as `Evidence`/`EvidenceId`/`Source` in `product_research/evidence.py`. `EvidenceKind` is the existing public research-kind vocabulary in `product_research/evidence_policy.py`. There is no runtime acquisition code, provider dependency, persistence layer, async execution model, or global Evidence-ID allocator to integrate with.

ECO-13 therefore needs to define a narrow control-plane seam that future ECO-14 adapters can implement without moving normalization or Evidence ownership into provider code. The core must also express the difference between acquisition absence and an Evidence fact, and between execution coverage and downstream commercial sufficiency.

## Goals / Non-Goals

**Goals:**

- Provide one small standard-library-only orchestration module with immutable value objects and one fail-closed run entry point.
- Make planner, acquisition, and normalization behavior caller-supplied while keeping plan traversal, ID allocation, failure aggregation, coverage, and overall status kernel-owned.
- Return enough ordered execution detail to explain partial results and replay equivalence without adding persistence or a wire protocol.
- Reuse `Evidence`, `EvidenceId`, `Source`, and `EvidenceKind` directly and validate normalized output through the existing Evidence structural boundary.

**Non-Goals:**

- Source-specific adapters, provider syntax, HTTP, scraping, credentials, retry/backoff, caching, rate limiting, concurrency, and persistence.
- Evidence Policy eligibility, Evidence Assessment, research semantics, commercial completeness, qualitative scores, Unit Economics, Risk, Red Team, reports, or decision labels.
- Global/cross-run Evidence identity, a second Evidence draft/schema, a plugin registry, or automatic planner/normalizer implementations.

## Decisions

### 1. Keep the capability in one sibling module

Add only `product_research/research_orchestration.py` for the production capability. It will contain the small public input/result types and the orchestration function because none has an independently used runtime caller yet. The expected public surface is:

```text
ResearchObjective
ResearchTask
ResearchPlan
RawFinding
AcquisitionResult
TaskStatus
FailureReason
ResearchFailure
TaskResult
RunStatus
ResearchRunResult
run_research(objective, planner, acquire, normalize)
```

`ResearchObjective` contains only a non-empty stable `objective_id` and non-empty objective text. `ResearchTask` contains `task_id`, `research_question`, `source_family`, `query_intent`, existing `EvidenceKind`, and `required`. `ResearchPlan` binds one `objective_id` to an ordered task tuple. Strings are validated without trimming or silent repair; callers must provide canonical values.

Alternative considered: split planner, executor, state, and normalizer into packages. Rejected because ECO-13 has one consumer path and no evidence of independently evolving implementations; injected callables already provide the replaceable seams.

### 2. Use narrow synchronous callable ports

The entry point accepts boundaries equivalent to:

```text
planner(ResearchObjective) -> ResearchPlan
acquire(ResearchTask) -> AcquisitionResult
normalize(ResearchTask, RawFinding, EvidenceId) -> Evidence
```

The kernel calls the planner once, then calls acquisition sequentially in task order. It does not define base adapter classes, registries, async protocols, dependency injection containers, or default implementations. Tests use small functions or callable fakes. Ordinary exceptions from a boundary become structured run failures; `KeyboardInterrupt`, `SystemExit`, and other `BaseException` subclasses are not swallowed.

Alternative considered: publish abstract base classes or `Protocol` hierarchies. Rejected because call signatures are sufficient for this local boundary and avoid speculative framework surface. Async execution was rejected because deterministic completion reconciliation and concurrency policy are explicitly outside ECO-13.

### 3. Keep RawFinding minimal and non-durable

`RawFinding` contains a non-empty task-local `finding_id`, non-empty raw text `content`, an existing `Source`, an explicit canonical UTC whole-second `observed_at`, and JSON-compatible `metadata`. Source publication/effective dates or adapter-specific values can be retained in metadata until the normalizer maps them to the existing Evidence fields and policy metadata. Raw findings never contain an `EvidenceId`, Tier, Evidence Status, or Confidence.

The value validates and defensively copies JSON metadata but has no serializer or persistence promise. This makes it an acquisition transfer object rather than another Evidence model. The normalizer remains replaceable because semantic mapping of raw content to claim/evidence/tier/status/confidence is caller-owned; ECO-13 owns only when and with which ID it is called.

Alternative considered: introduce a public pre-ID Evidence draft. Rejected because it would duplicate nearly every Evidence field and create the competing Evidence-producing layer the ECO-13/ECO-14 boundary forbids. An untyped arbitrary payload was also rejected because it would prevent deterministic structural validation of acquisition outputs.

### 4. Separate adapter status from normalized task outcome with one closed vocabulary

`TaskStatus` is closed to `SUCCESS`, `PARTIAL`, `UNAVAILABLE`, and `FAILED`. `AcquisitionResult` accepts only `SUCCESS`, `UNAVAILABLE`, or `FAILED`: success carries an ordered tuple of findings, while unavailable/failed carries none. `PARTIAL` is kernel-produced only when at least one finding from a task normalizes and at least one fails. A successful acquisition with zero findings is structurally valid and has task status `SUCCESS`; it proves execution occurred but does not fabricate Evidence.

`FailureReason` is a small closed vocabulary covering `PLANNER_EXCEPTION`, `INVALID_PLAN`, `ACQUISITION_UNAVAILABLE`, `ACQUISITION_FAILED`, `ACQUISITION_EXCEPTION`, `INVALID_ACQUISITION_RESULT`, `NORMALIZATION_EXCEPTION`, and `INVALID_EVIDENCE`. `ResearchFailure` carries the reason plus optional task/finding identities. It intentionally carries no provider-specific error taxonomy or arbitrary exception text. `TaskResult` preserves each task, final task status, declared finding IDs, successful Evidence IDs, and ordered failures.

A planner exception or invalid plan returns a `FAILED` `ResearchRunResult` with no plan, tasks, or Evidence and the applicable run-level failure. Strict constructors can reject malformed caller-created values, while the public runner still validates returned boundary objects defensively in case a fake, adapter, or corrupted instance bypasses normal construction.

Alternative considered: use exceptions as the public execution result. Rejected because unavailable acquisition and partial completion are expected research states that must coexist with successful Evidence. Source-specific reason enums were deferred to ECO-14 because they would couple the kernel to providers.

### 5. Validate identities before consuming result content

Plan task IDs must be unique and the plan's objective ID must equal the requested objective ID. Each acquisition result's task ID must exactly equal the current task ID. Finding IDs must be valid and unique within that task; the same task-local finding ID may appear under another task because ordering and the owning task disambiguate it. Any invalid or mismatched result fails the whole task before normalization, so a malformed result cannot partially publish untrusted content.

Results and diagnostics remain in plan order; within a task they remain in finding order. No lexical sort is used for execution. Coverage and failed-task tuples are filtered from plan order, making identity checks and output ordering independently reproducible.

Alternative considered: silently bind a mismatched result to the current task or deduplicate findings. Rejected because either repair hides adapter defects and changes which observation receives an Evidence ID.

### 6. Allocate IDs by finding position before normalization

The kernel owns a run-local counter starting at one and creates existing `EvidenceId` values formatted as `E001`, `E002`, and onward. It advances once for every structurally accepted raw finding visited in plan/finding order before invoking normalization. Normalization failure therefore leaves a deterministic gap and never shifts IDs assigned to later findings.

The normalizer output is accepted only when its concrete type is the existing `Evidence`, its ID exactly equals the allocated ID, and `Evidence.from_json(output.to_json())` reconstructs an equal structurally valid value. Any exception or mismatch becomes a failure for that finding; there is no repair, ID replacement, or alternate internal Evidence representation.

Alternative considered: allocate only after successful normalization. Rejected because later IDs would depend on which earlier normalizers happened to succeed, making a finding's ID unstable across failure diagnosis. Content hashes were rejected because canonical global identity and collision policy are outside scope.

### 7. Derive coverage and run status from explicit ordered outcomes

`ResearchRunResult` retains the valid objective, optional valid plan, ordered task results, ordered accepted Evidence, ordered failures, and the four coverage tuples:

```text
required_task_ids
covered_required_task_ids
missing_required_task_ids
failed_task_ids
```

A required task is covered only when its final `TaskStatus` is `SUCCESS`. `PARTIAL`, `UNAVAILABLE`, and `FAILED` tasks appear in `failed_task_ids`; required ones also appear in `missing_required_task_ids`. Optional failures stay visible but do not reduce required coverage.

Run status uses this fixed precedence:

1. No accepted Evidence → `FAILED`.
2. Accepted Evidence plus one or more missing required tasks → `PARTIAL`.
3. Accepted Evidence and no missing required tasks → `COMPLETE`.

This intentionally allows a successfully executed zero-finding task to count as covered while the run is still `FAILED` if no task produced Evidence. Coverage answers whether declared work completed; run failure answers whether the run yielded anything usable. Neither answers whether the evidence is commercially sufficient.

Alternative considered: make any optional failure force `PARTIAL`. Rejected because the requested completeness contract is explicitly required-task coverage. Treating zero findings as Unknown Evidence or renormalizing status based on commercial expectations was rejected as fabricated analysis.

### 8. Make replay equivalence structural

All public aggregate collections are tuples, all status/reason values are closed immutable values, metadata is defensively normalized, and no system clock, randomness, environment input, persistence, or asynchronous completion order is consulted. Equality of the immutable values therefore gives the replay test: equivalent objective, plan, fake results, and normalized Evidence yield an equivalent `ResearchRunResult`.

No JSON serialization is added for orchestration values because there is no persistence or wire consumer. Replay-friendly means deterministic structural results in this Change, not a stored replay subsystem.

Alternative considered: add run IDs, timestamps, and serialization now. Rejected because they require external namespace/clock/persistence policies and would make equivalent deterministic runs differ.

### 9. Freeze the ECO-14 boundary at acquisition results

Future search, marketplace, consumer/social, supplier, and regulatory/IP adapters accept a `ResearchTask` and return `AcquisitionResult`/`RawFinding`. They do not receive final Evidence IDs and do not return durable Evidence. The ECO-13 normalizer boundary is the only route from those raw findings into the existing Phase 3 Evidence contract.

The module imports `EvidenceKind` only as vocabulary and does not call Evidence Policy. It imports the existing Evidence structural types only for construction validation. Static ownership tests will guard against network, HTTP, async, LLM, persistence, Unit Economics, scoring, or analysis imports/calls.

Alternative considered: let every adapter normalize its own output into Evidence. Rejected because that duplicates ID allocation and Evidence-producing semantics across source families and makes cross-adapter ordering dependent on provider code.

## Risks / Trade-offs

- [A successful task can return zero findings and count as covered] → The run still becomes `FAILED` when no Evidence exists; this preserves the distinction between executed coverage and factual output without inventing a no-result fact.
- [Position-based IDs can contain gaps after normalization failures] → Gaps are intentional evidence of deterministic attempted positions and prevent later identities from shifting.
- [Free-form source-family and query-intent strings are not typo-proof] → ECO-13 validates non-empty exact values but avoids freezing provider vocabulary before ECO-14; plan authors own canonical naming.
- [JSON metadata is less strongly typed than core fields] → It is acquisition-only, validated and copied, and final durable typing remains enforced by the existing Evidence contract.
- [Exact Evidence serialization round-trip adds validation work] → Runs are deliberately sequential and small; fail-closed structural integrity is more important than optimizing an unmeasured acquisition-control path.
- [A planner failure yields a result without a plan] → Keeping the objective and explicit failure provides a total public run outcome without pretending a valid plan existed.

## Migration Plan

1. Add focused RED tests for value validation, identity integrity, nested ordering/ID allocation, each acquisition and normalization failure, coverage/status precedence, replay equality, and ownership exclusions.
2. Add the single orchestration module and make the focused suite GREEN without modifying existing Evidence, policy, assessment, economics, or scoring behavior.
3. Narrowly update `tests/scenarios.md` and capability-routing statements only where they would otherwise misstate the new production boundary.
4. Run the focused orchestration suite, every existing Phase 3/4 suite, full test discovery, strict Change/all OpenSpec validation, and a final scope/forbidden-dependency audit.

Rollback removes the new module, focused tests, and narrow documentation updates. No stored state, dependency, provider, or existing contract requires migration.
