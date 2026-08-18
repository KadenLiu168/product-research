## MODIFIED Requirements

### Requirement: Evidence kinds and policy metadata are explicit
The project policy SHALL support explicit policy kinds for market or competition data, marketplace price, supplier quotation, VOC, regulation, certification, tariff, authoritative IP records, and long-term industry data. The authoritative IP-record kind SHALL be exactly `ip_authoritative_record` and SHALL represent official patent or trademark records without classifying them as regulation. The kind and its temporal fields SHALL be read from `metadata.policy`; an absent or unsupported kind SHALL reject with `UNSUPPORTED_EVIDENCE_KIND`. Date-sensitive kinds SHALL require policy metadata rather than interpreting `observed_at` as a publication, review, quotation, issue, effective, or verification date. Required dates SHALL use strict ISO calendar dates, and current-version verification instants SHALL use timezone-aware timestamps. Missing required temporal metadata SHALL reject with `MISSING_FRESHNESS_METADATA`; malformed, future, or semantically inconsistent policy dates SHALL reject with a stable policy-metadata reason code.

#### Scenario: Freshness-sensitive Evidence lacks source date
- **WHEN** marketplace, market, competition, supplier, or VOC Evidence lacks its required source date in `metadata.policy`
- **THEN** validation returns `REJECT` with `MISSING_FRESHNESS_METADATA` without substituting `observed_at`

#### Scenario: Authoritative IP record has a truthful kind
- **WHEN** official patent or trademark Evidence declares `metadata.policy.kind` as `ip_authoritative_record`
- **THEN** the kind is recognized without representing the Evidence as regulation

#### Scenario: Unsupported Evidence kind fails closed
- **WHEN** `metadata.policy.kind` is not supported by the supplied policy
- **THEN** validation returns `REJECT` with `UNSUPPORTED_EVIDENCE_KIND`

## ADDED Requirements

### Requirement: Current authoritative IP records require authoritative verification
Authoritative IP-record Evidence SHALL use `metadata.policy.kind = ip_authoritative_record`, a Source registered as official or authoritative, and `Tier 1`. Its `metadata.policy` SHALL contain an `effective_from` date representing the record's applicable issue, registration, filing, publication, or other caller-selected authoritative start date, and a `verified_current_at` instant confirming the record's current authoritative state. For `CURRENT` use, `effective_from` SHALL not be after `as_of`, `verified_current_at` SHALL not be after `as_of`, `effective_from` SHALL not be after `verified_current_at`, and verification age SHALL not exceed the supplied Policy's explicit maximum current-verification age. Missing current-version metadata SHALL reject with `MISSING_FRESHNESS_METADATA`; non-authoritative sources, Tier mismatch, future or inconsistent metadata, and expired verification SHALL reject under the existing stable Policy reason codes. This kind SHALL NOT claim that a record is legally dispositive, unexpired, enforceable, infringed, or applicable beyond the proposition and metadata the caller explicitly supplies.

#### Scenario: Current official patent record is accepted
- **WHEN** an official Tier-1 patent record has a declared applicable date on or before `as_of` and authoritative current-state verification within the Policy window
- **THEN** it may return `ACCEPT_CURRENT` and be fact eligible for the caller's declared proposition

#### Scenario: Current official trademark record is accepted
- **WHEN** an official Tier-1 trademark record satisfies the same current-verification metadata and Policy rules
- **THEN** it may return `ACCEPT_CURRENT` without being labeled as regulation

#### Scenario: Stale authoritative IP verification is rejected
- **WHEN** an authoritative IP record's `verified_current_at` exceeds the maximum current-verification age for `CURRENT` use
- **THEN** validation returns `REJECT` with `STALE_EVIDENCE`

#### Scenario: Secondary IP summary is not authoritative support
- **WHEN** `ip_authoritative_record` Evidence uses a registered non-authoritative Source or a non-Tier-1 tier
- **THEN** validation returns `REJECT` with the existing Source or tier reason code

#### Scenario: IP metadata does not infer legal conclusions
- **WHEN** a structurally and temporally valid authoritative IP record is accepted
- **THEN** Policy acceptance establishes only Evidence eligibility and does not infer infringement, enforceability, expiration, product applicability, or a Risk classification
