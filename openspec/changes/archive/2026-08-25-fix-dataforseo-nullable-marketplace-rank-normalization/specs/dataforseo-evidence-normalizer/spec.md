## MODIFIED Requirements

### Requirement: Normalization validates only owned recognition and provenance consistency
Before construction, the capability SHALL require a valid DataForSEO provider identity, one supported operation, a `Source.source_type` equal to that operation, the operation's existing SEARCH or MARKETPLACE family equal to `task.source_family`, the owning research task and finding identities, and the operation-specific acquisition provenance needed for durable traceability. When provider, operation, source type, finding identity, content, observation, or ordering provenance is represented more than once, those representations MUST agree exactly. For `amazon_products_live`, both duplicated rank representations MUST be present and their value types and values MUST match exactly; equal provider-validated values, including `metadata.provider_rank = null` and `metadata.observation.rank_absolute = null`, are valid normalization provenance. Contradictory, absent, or malformed normalization-owned provenance MUST fail closed and MUST NOT be silently repaired. The capability MUST preserve accepted rank values unchanged and MUST NOT reproduce the provider-owned full response schema, endpoint protocol, provider-native rank type/schema rules, or metric-field validation already completed before `RawFinding` creation.

#### Scenario: Contradictory source operation fails closed
- **WHEN** metadata declares one supported operation while `Source.source_type` or canonical content declares another
- **THEN** normalization raises an ordinary exception and creates no Evidence

#### Scenario: Operation family mismatch fails closed
- **WHEN** a SEARCH operation is paired with a MARKETPLACE task or `amazon_products_live` is paired with a SEARCH task
- **THEN** normalization raises an ordinary exception rather than overriding the task family

#### Scenario: Missing durable provenance fails closed
- **WHEN** required research identity, provider task identity, endpoint, request context, operation-specific ordering, or factual observation provenance is absent or malformed
- **THEN** normalization fails without repairing or synthesizing the missing value

#### Scenario: Provider protocol remains provider-owned
- **WHEN** a valid provider-produced RawFinding reaches normalization
- **THEN** normalization checks recognition, required durable provenance presence, and duplicated provenance consistency but does not rerun complete response-schema, provider-native rank type/schema, or metric-field validation

#### Scenario: Nullable provider-owned Amazon rank remains valid provenance
- **WHEN** a valid provider-produced `amazon_products_live` RawFinding contains both `metadata.provider_rank = null` and `metadata.observation.rank_absolute = null`
- **THEN** normalization succeeds, preserves both nulls unchanged in the exact Evidence factual basis and acquisition metadata, and returns Evidence with the existing `Observed` status

#### Scenario: Rank provenance contradiction fails closed
- **WHEN** an `amazon_products_live` RawFinding contains both required rank provenance representations but their value types differ or their values are not equal
- **THEN** normalization raises an ordinary exception through the existing normalization failure semantics and does not synthesize, coerce, or repair either value

#### Scenario: Required rank provenance absence fails closed
- **WHEN** an `amazon_products_live` RawFinding omits either `metadata.provider_rank` or `metadata.observation.rank_absolute`
- **THEN** normalization raises an ordinary exception rather than treating null as absence or synthesizing a rank
