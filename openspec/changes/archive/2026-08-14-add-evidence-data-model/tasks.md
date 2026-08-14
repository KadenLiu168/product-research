## 1. Confirm the implementation boundary

- [x] 1.1 Re-read the repository runtime and dependency manifests at Apply time, select the smallest supported module and test layout, and record the evidence-backed choice and exact focused test command in `design.md` before adding implementation code.
- [x] 1.2 Create failing contract tests for valid construction, required fields, blank/wrong/extra fields, Evidence ID syntax, structured Source behavior, all accepted tier/status/confidence values, invalid constrained values, and canonical `observed_at`; run them and record the expected RED result.
- [x] 1.3 Create failing contract tests for JSON-compatible metadata, invalid metadata, deterministic JSON bytes, strict deserialization, semantic equality, and serialize-deserialize-serialize round trips; run them and record the expected RED result.

## 2. Implement the minimal shared contract

- [x] 2.1 Implement the constrained Evidence ID, tier, status, and confidence value types plus the policy-neutral Source model, with explicit failures and no coercion, inference, allocator, or policy logic; make the focused value/source tests pass.
- [x] 2.2 Implement the Evidence model, canonical UTC observation-time validation, and recursive JSON-compatible metadata validation with exactly the required core fields; make the construction, timestamp, and metadata tests pass.
- [x] 2.3 Implement deterministic JSON serialization and strict deserialization using the specified field order, metadata key ordering, escaping/finite-number behavior, and rejection rules; make serialization, deserialization, repeated-output, and round-trip tests pass.

## 3. Integrate and verify the contract

- [x] 3.1 Update only the necessary living documentation to point Evidence producers and downstream consumers to the shared contract and Evidence ID reference boundary without duplicating or implementing Evidence Policy, conflict/confidence, Research, Analysis, Scoring, Gate, Report, or Persistence logic.
- [x] 3.2 Run the focused contract suite and every existing repository-wide automated validation applicable to the selected runtime, then confirm tests cover every requirement scenario and that repeated serialization is byte-stable.
- [x] 3.3 Run `openspec validate add-evidence-data-model --strict` and `openspec validate --all --strict`, inspect the final diff for undeclared dependencies, domain-specific fields, policy inference, persistence, adapters, scoring/gates, and unrelated changes, and leave all checks green before marking the Change implemented.

## 4. Review remediation

- [x] 4.1 Require an explicit `Source.title` constructor argument while preserving explicit `title=None`, and add regression coverage for omission versus null.
- [x] 4.2 Revalidate mutable metadata recursively at the JSON serialization boundary and add regression coverage for post-construction invalid key mutation.
- [x] 4.3 Reject non-UTF-8-encodable core, Source, constrained, and metadata strings/keys, including lone surrogates from JSON deserialization; add regression coverage.
- [x] 4.4 Run the focused/full validation and both strict OpenSpec validators, inspect the remediation diff, and leave all checks green.
- [x] 4.5 Revalidate mutable `EvidenceId`, `Tier`, `Status`, and `Confidence` values at the JSON serialization boundary and add regression coverage for post-construction `.value` rebinding.
- [x] 4.6 Run the focused/full validation and both strict OpenSpec validators for the constrained-value mutation remediation, inspect the diff, and leave all checks green.
- [x] 4.7 Make `EvidenceId`, `Tier`, `Status`, and `Confidence` values immutable after construction while preserving read access, and prove hash/key stability with regression coverage.
- [x] 4.8 Add the explicit wrong-case JSON confidence scenario, run focused/full validation and both strict OpenSpec validators, and inspect the final remediation diff.
