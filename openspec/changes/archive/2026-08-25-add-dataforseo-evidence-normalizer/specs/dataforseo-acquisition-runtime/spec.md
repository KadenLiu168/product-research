## MODIFIED Requirements

### Requirement: Runtime remains an external acquisition-layer capability
All runtime and provider implementation SHALL remain outside `product_research/`. No module under `product_research/` SHALL import the DataForSEO runtime or normalizer, while those external capabilities MAY depend on the existing core contracts. The runtime output SHALL continue to stop at existing `AcquisitionResult` and ordered `RawFinding` values and SHALL NOT bundle or invoke normalization. A separate external ECO-45 DataForSEO normalizer SHALL be available for callers to pass those supported raw findings through the existing `run_research` normalization seam into existing durable Evidence. Capability and Skill documentation SHALL distinguish provider-owned SEARCH/MARKETPLACE acquisition from the separate normalization path, identify intentionally absent or unsupported families as unavailable, and MUST NOT claim automatic Evidence Policy, Evidence Assessment, structured analysis, or full 16-stage workflow execution.

#### Scenario: Core dependency direction remains one-way
- **WHEN** repository imports are inspected after implementation
- **THEN** the external runtime and normalizer may import core contracts but no `product_research/` module imports concrete DataForSEO code

#### Scenario: Runtime stops before ECO-45 normalization
- **WHEN** successful DataForSEO findings leave the composed runtime
- **THEN** they remain the existing raw findings until a caller separately supplies the ECO-45 normalizer through the existing orchestration seam

#### Scenario: Documentation states availability narrowly
- **WHEN** OpenSpec and Skill documentation is inspected
- **THEN** it describes configured DataForSEO SEARCH and MARKETPLACE acquisition plus the separate RawFinding-to-Evidence normalization path without claiming unsupported families or automatic downstream workflow execution
