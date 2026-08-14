## ADDED Requirements

### Requirement: Shared Evidence record
The system SHALL provide one shared Evidence record with required fields `id`, `claim`, `evidence`, `source`, `observed_at`, `tier`, `status`, `confidence`, and `metadata`. `claim` SHALL state the fact or proposition being supported, while `evidence` SHALL contain the distinct observed, quoted, or inferential basis for that claim. The system SHALL reject missing fields, null core fields other than `source.title`, wrong field types, blank required strings, and undeclared top-level fields.

#### Scenario: Construct a complete Evidence record
- **WHEN** a caller supplies valid values for every declared Evidence field
- **THEN** the system constructs an Evidence value that preserves the claim separately from its supporting evidence content

#### Scenario: Reject an incomplete Evidence record
- **WHEN** a caller omits a required field or supplies an undeclared top-level field
- **THEN** the system rejects the record explicitly without supplying a factual default

### Requirement: Stable Evidence ID
The system SHALL represent an Evidence ID as `E` followed by at least three decimal digits whose numeric portion is not all zeroes. The system SHALL preserve leading zeroes and SHALL reject whitespace, other prefixes, signs, separators, non-digits, and all-zero identifiers. The model SHALL NOT allocate IDs or claim global uniqueness outside the record boundary.

#### Scenario: Accept a report-style Evidence ID
- **WHEN** a caller constructs an Evidence ID from `E001`
- **THEN** the system accepts it and preserves the serialized value as `E001`

#### Scenario: Reject an invalid Evidence ID
- **WHEN** a caller supplies `E000`, `1`, `E-01`, or a value with surrounding whitespace
- **THEN** the system rejects the identifier explicitly without rewriting it

### Requirement: Structured Source representation
The system SHALL represent `source` as an object containing required fields `provider`, `source_type`, `reference`, and `title`. `provider`, `source_type`, and `reference` SHALL be non-empty strings; `reference` SHALL accept either a URL or another stable source identifier without assuming a web source. `title` SHALL be either a non-empty string or null. The model SHALL NOT infer tier, quality, independence, or claim support from Source fields.

#### Scenario: Represent a URL source
- **WHEN** a caller supplies a provider, a source type, a URL reference, and a title
- **THEN** the system preserves all four values as structured Source provenance

#### Scenario: Represent a non-web source without an invented title
- **WHEN** a caller supplies a provider, source type, stable document reference, and null title
- **THEN** the system accepts the Source without inventing a URL, title, tier, or quality judgment

#### Scenario: Reject an unstructured source
- **WHEN** a caller supplies only a free-text source string or an extra undeclared Source field
- **THEN** the system rejects the Source explicitly

### Requirement: Closed Evidence tier values
The system SHALL accept exactly `Tier 1`, `Tier 2`, `Tier 3`, and `Tier 4` as Evidence tier values. The model SHALL NOT derive a tier from Source data or validate whether an assigned tier is policy-appropriate.

#### Scenario: Accept every defined tier
- **WHEN** a caller supplies each of the four defined tier values
- **THEN** the system accepts each value without changing it

#### Scenario: Reject an unsupported tier
- **WHEN** a caller supplies an integer, null, `Tier 5`, an alias, or different casing
- **THEN** the system rejects the value without selecting a fallback tier

### Requirement: Closed Evidence status values
The system SHALL accept exactly `Observed`, `Estimated`, `Calculated`, and `Unknown` as Evidence status values. Each value SHALL remain distinct, and the model SHALL NOT infer, upgrade, downgrade, or default a status.

#### Scenario: Preserve every defined status
- **WHEN** otherwise equivalent Evidence records use each of the four defined statuses
- **THEN** the system preserves four distinct status values through the model and JSON boundary

#### Scenario: Reject an unsupported status
- **WHEN** a caller supplies null, a missing value, an alias, or a status with different casing
- **THEN** the system rejects the value without converting it to `Observed` or another status

### Requirement: Closed confidence values
The system SHALL accept exactly `High`, `Medium`, and `Low` as confidence values. The model SHALL NOT calculate, infer, revise, downgrade, or default confidence.

#### Scenario: Accept every defined confidence
- **WHEN** a caller supplies each of the three defined confidence values
- **THEN** the system accepts and preserves each value

#### Scenario: Reject an unsupported confidence
- **WHEN** a caller supplies null, a missing value, a number, an alias, or different casing
- **THEN** the system rejects the value without selecting `High` or another fallback

### Requirement: Unambiguous observation time
The system SHALL define `observed_at` as the instant when the Evidence content was observed or confirmed by its producer, not the source publication, issue, or effective date. Its JSON value SHALL use canonical RFC 3339 UTC whole-second form `YYYY-MM-DDTHH:MM:SSZ`. The system SHALL reject date-only values, timestamps without a timezone, non-UTC offsets, fractional seconds, and malformed timestamps.

#### Scenario: Accept a canonical observation time
- **WHEN** a caller supplies `2026-08-14T08:30:00Z`
- **THEN** the system accepts it as the Evidence observation instant and serializes the same canonical value

#### Scenario: Reject an ambiguous Evidence date
- **WHEN** a caller supplies `2026-08-14`, a local time without an offset, or a non-canonical timestamp
- **THEN** the system rejects the value instead of guessing its timezone or meaning

### Requirement: JSON-compatible metadata extension
The system SHALL represent `metadata` as an explicit JSON object with non-empty string keys and values limited to JSON nulls, booleans, finite numbers, strings, arrays, and nested objects. The system SHALL reject non-JSON runtime values, non-finite numbers, non-object metadata roots, and empty metadata keys. Metadata SHALL NOT override or change the semantics of core fields.

#### Scenario: Preserve domain metadata
- **WHEN** a caller supplies nested JSON-compatible metadata such as currency, market, units, sample size, or a raw numeric value
- **THEN** the system preserves that metadata without adding domain fields to the Evidence core

#### Scenario: Reject non-portable metadata
- **WHEN** metadata contains a non-JSON runtime object, a non-finite number, or an empty key
- **THEN** the system rejects the Evidence record explicitly

### Requirement: Deterministic JSON serialization
The system SHALL serialize Evidence as UTF-8 JSON using the documented fixed top-level and Source field order, recursively lexicographic metadata object-key order, no insignificant whitespace, and one documented escaping and finite-number strategy. Serializing the same Evidence value repeatedly SHALL produce byte-identical output and SHALL include every declared field, including an empty `metadata` object and nullable `source.title`.

#### Scenario: Serialize a complete Evidence value
- **WHEN** a caller serializes a valid Evidence value
- **THEN** the output contains exactly the declared wire fields and their preserved values in canonical order

#### Scenario: Repeat serialization deterministically
- **WHEN** a caller serializes the same Evidence value multiple times, including nested metadata whose input key order differs
- **THEN** every output is byte-identical and nested metadata keys appear in lexicographic order

### Requirement: Strict JSON deserialization
The system SHALL deserialize valid contract JSON into the shared Evidence and Source value types. It SHALL reject malformed JSON, missing or extra fields, wrong primitive or container types, invalid IDs, invalid timestamps, invalid constrained values, and invalid metadata without coercing or substituting values.

#### Scenario: Deserialize valid contract JSON
- **WHEN** a caller deserializes JSON containing every required field and valid value
- **THEN** the system reconstructs the corresponding typed Evidence value

#### Scenario: Reject invalid contract JSON
- **WHEN** JSON contains an unknown status, string confidence where casing is wrong, numeric tier, extra top-level field, or malformed observation time
- **THEN** deserialization fails explicitly and returns no partially defaulted Evidence value

### Requirement: Semantic round-trip stability
For every valid Evidence value, deserializing its serialized representation SHALL produce an equivalent Evidence value across all core fields, Source fields, constrained values, observation time, and metadata. Serializing that reconstructed value SHALL reproduce the same canonical JSON bytes.

#### Scenario: Round trip a representative Evidence value
- **WHEN** a valid Evidence value with structured Source and nested metadata is serialized, deserialized, and serialized again
- **THEN** the reconstructed value equals the original and the second JSON output is byte-identical to the first

### Requirement: Evidence references are ID-based
The shared contract SHALL expose the Evidence ID value for downstream reference by findings, scores, gate results, Red Team revisions, and reports. This capability SHALL NOT define those downstream models, duplicate Evidence records inside them, allocate IDs, or enforce cross-collection referential integrity.

#### Scenario: Reference Evidence without redefining it
- **WHEN** a later module needs to associate a result with supporting Evidence
- **THEN** it can retain the Evidence ID value while the Evidence record remains governed by this shared contract

### Requirement: Model validity is separate from Evidence Policy
The model SHALL restrict only representational validity. It SHALL NOT perform provider-to-tier inference, tier/source consistency checks, source-quality judgment, freshness thresholds, stale-evidence detection, citation completeness checks, source-independence detection, conflict handling, confidence calculation, research acquisition, scoring, gates, analysis, or report generation.

#### Scenario: Preserve a structurally valid policy question
- **WHEN** an Evidence record is structurally valid but a later policy may question its assigned tier, freshness, confidence, or source quality
- **THEN** the model accepts the representation without declaring the Evidence policy-acceptable
