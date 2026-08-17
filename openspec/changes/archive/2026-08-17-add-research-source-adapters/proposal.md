## Why

ECO-13 established the deterministic acquisition seam but intentionally left `ResearchTask.source_family` free-form and provided no production family dispatcher. ECO-14 must now close the Phase 5 acquisition architecture so five source families can plug into that seam consistently without adding provider clients or a second Evidence-producing path.

## What Changes

- Add a closed source-family vocabulary containing exactly `SEARCH`, `MARKETPLACE`, `CONSUMER_SOCIAL`, `SUPPLIER`, and `REGULATORY_IP`.
- **BREAKING**: require `ResearchTask.source_family` to be an exact closed source-family value rather than an arbitrary non-empty string.
- Add a small fixed-family `ResearchSourceAdapters` composition boundary with five explicit optional adapter slots; the composed value is directly callable as ECO-13's injected `acquire` boundary.
- Return a matching-task `UNAVAILABLE` acquisition result with zero findings when the requested valid family has no configured adapter.
- Pass configured adapter results through unchanged and leave explicit failure, ordinary-exception conversion, malformed-result validation, finding normalization, and Evidence ID allocation under the existing ECO-13 orchestration contract.
- Narrowly align capability documentation and acceptance scenarios to distinguish an implemented family-level adapter contract from still-unimplemented provider-backed acquisition.

## Capabilities

### New Capabilities

- `research-source-adapters`: Defines the fixed five-family adapter composition, deterministic routing, missing-capability behavior, and the acquisition-only ownership boundary.

### Modified Capabilities

- `research-orchestration`: Replaces the free-form task source-family field with the closed five-family vocabulary and makes the implemented ECO-14/ECO-13 ownership boundary explicit.

## Impact

- Expected new production module: `product_research/research_adapters.py`.
- Expected focused tests: `tests/test_research_adapters.py`, plus narrow updates to `tests/test_research_orchestration.py` for the closed task field.
- Expected modified orchestration surface: `SourceFamily` and `ResearchTask.source_family` in `product_research/research_orchestration.py`; existing acquisition, normalization, failure, ordering, coverage, and run-status behavior otherwise remains unchanged.
- `tests/scenarios.md`, `SKILL.md`, and `docs/product-research-skill-spec.md` may receive only the truth-alignment edits needed to route the new contract while continuing to state that concrete provider-backed research is unavailable.
- No external dependencies, network or browser clients, provider implementations, retries, caching, async execution, persistence, automatic planning/normalization, Evidence schema changes, policy/assessment execution, analysis, scoring, Red Team, reporting, or final recommendation generation are introduced.
