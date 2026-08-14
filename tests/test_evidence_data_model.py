import importlib
import json
import unittest


def _evidence_module():
    try:
        return importlib.import_module("product_research.evidence")
    except ModuleNotFoundError as exc:
        raise AssertionError("Evidence contract module has not been implemented") from exc


class EvidenceCoreContractTests(unittest.TestCase):
    def setUp(self):
        self.module = _evidence_module()

    def build_evidence(self, **overrides):
        values = {
            "id": self.module.EvidenceId("E001"),
            "claim": "Listed retail price is $39.99.",
            "evidence": "The product page displayed a listed price of $39.99.",
            "source": self.module.Source(
                provider="Example Marketplace",
                source_type="marketplace_listing",
                reference="https://example.test/products/123",
                title="Example product listing",
            ),
            "observed_at": "2026-08-14T08:30:00Z",
            "tier": self.module.Tier("Tier 2"),
            "status": self.module.Status("Observed"),
            "confidence": self.module.Confidence("Medium"),
            "metadata": {},
        }
        values.update(overrides)
        return self.module.Evidence(**values)

    def test_constructs_complete_record_and_keeps_claim_separate(self):
        record = self.build_evidence()

        self.assertEqual(record.claim, "Listed retail price is $39.99.")
        self.assertEqual(record.evidence, "The product page displayed a listed price of $39.99.")
        self.assertNotEqual(record.claim, record.evidence)

    def test_rejects_missing_required_field(self):
        with self.assertRaises((TypeError, ValueError)):
            self.module.Evidence(
                id=self.module.EvidenceId("E001"),
                claim="claim",
                evidence="basis",
                source=self.build_evidence().source,
                observed_at="2026-08-14T08:30:00Z",
                tier=self.module.Tier("Tier 2"),
                status=self.module.Status("Observed"),
            )

    def test_rejects_blank_core_string(self):
        with self.assertRaises((TypeError, ValueError)):
            self.build_evidence(claim="")

    def test_rejects_wrong_core_type(self):
        with self.assertRaises((TypeError, ValueError)):
            self.build_evidence(claim=39.99)

    def test_rejects_null_core_fields_except_nullable_source_title(self):
        for field in (
            "id",
            "claim",
            "evidence",
            "source",
            "observed_at",
            "tier",
            "status",
            "confidence",
            "metadata",
        ):
            with self.subTest(field=field), self.assertRaises((TypeError, ValueError)):
                self.build_evidence(**{field: None})

    def test_rejects_extra_core_field(self):
        with self.assertRaises((TypeError, ValueError)):
            self.module.Evidence(
                **{
                    "id": self.module.EvidenceId("E001"),
                    "claim": "claim",
                    "evidence": "basis",
                    "source": self.build_evidence().source,
                    "observed_at": "2026-08-14T08:30:00Z",
                    "tier": self.module.Tier("Tier 2"),
                    "status": self.module.Status("Observed"),
                    "confidence": self.module.Confidence("Medium"),
                    "metadata": {},
                    "extra": "rejected",
                }
            )

    def test_accepts_and_preserves_evidence_id_syntax(self):
        evidence_id = self.module.EvidenceId("E001")

        self.assertEqual(str(evidence_id), "E001")
        self.assertEqual(evidence_id, self.module.EvidenceId("E001"))

    def test_rejects_invalid_evidence_ids_without_rewriting(self):
        for invalid in ("E000", "1", "E-01", " E001", "E001 ", "X001", "E01"):
            with self.subTest(invalid=invalid), self.assertRaises((TypeError, ValueError)):
                self.module.EvidenceId(invalid)

    def test_preserves_structured_url_source(self):
        source = self.module.Source(
            provider="Example Marketplace",
            source_type="marketplace_listing",
            reference="https://example.test/products/123",
            title="Example product listing",
        )

        self.assertEqual(source.provider, "Example Marketplace")
        self.assertEqual(source.source_type, "marketplace_listing")
        self.assertEqual(source.reference, "https://example.test/products/123")
        self.assertEqual(source.title, "Example product listing")

    def test_accepts_non_web_source_with_null_title(self):
        source = self.module.Source(
            provider="Example Archive",
            source_type="document",
            reference="archive:document-123",
            title=None,
        )

        self.assertIsNone(source.title)
        self.assertEqual(source.reference, "archive:document-123")

    def test_requires_source_title_argument_even_when_title_is_nullable(self):
        with self.assertRaises(TypeError):
            self.module.Source(
                provider="Example Archive",
                source_type="document",
                reference="archive:document-123",
            )

        self.assertIsNone(
            self.module.Source(
                provider="Example Archive",
                source_type="document",
                reference="archive:document-123",
                title=None,
            ).title
        )

    def test_rejects_unstructured_or_extra_source_fields(self):
        with self.assertRaises((TypeError, ValueError)):
            self.module.Source("free-text source")

        with self.assertRaises((TypeError, ValueError)):
            self.module.Source(
                provider="provider",
                source_type="document",
                reference="doc-1",
                title=None,
                extra="rejected",
            )

    def test_rejects_blank_or_wrong_source_fields(self):
        for field in ("provider", "source_type", "reference"):
            with self.subTest(field=field), self.assertRaises((TypeError, ValueError)):
                self.module.Source(
                    provider="" if field == "provider" else "provider",
                    source_type="" if field == "source_type" else "document",
                    reference="" if field == "reference" else "doc-1",
                    title=None,
                )

        with self.assertRaises((TypeError, ValueError)):
            self.module.Source(
                provider="provider",
                source_type="document",
                reference="doc-1",
                title=42,
            )

    def test_accepts_every_defined_tier(self):
        for value in ("Tier 1", "Tier 2", "Tier 3", "Tier 4"):
            with self.subTest(value=value):
                self.assertEqual(str(self.module.Tier(value)), value)

    def test_accepts_every_defined_status(self):
        for value in ("Observed", "Estimated", "Calculated", "Unknown"):
            with self.subTest(value=value):
                self.assertEqual(str(self.module.Status(value)), value)

    def test_accepts_every_defined_confidence(self):
        for value in ("High", "Medium", "Low"):
            with self.subTest(value=value):
                self.assertEqual(str(self.module.Confidence(value)), value)

    def test_rejects_invalid_constrained_values_without_fallback(self):
        for constructor, invalid_values in (
            (self.module.Tier, (1, None, "Tier 5", "tier 1")),
            (self.module.Status, (None, "Observed-ish", "observed")),
            (self.module.Confidence, (None, 1, "medium")),
        ):
            for invalid in invalid_values:
                with self.subTest(constructor=constructor.__name__, invalid=invalid), self.assertRaises(
                    (TypeError, ValueError)
                ):
                    constructor(invalid)

    def test_constrained_values_are_read_only_and_hash_stable(self):
        cases = (
            (self.module.EvidenceId("E001"), "E000"),
            (self.module.Tier("Tier 2"), "Tier 5"),
            (self.module.Status("Observed"), "observed"),
            (self.module.Confidence("Medium"), "medium"),
        )
        for value, invalid in cases:
            with self.subTest(value=repr(value)):
                original_hash = hash(value)
                lookup = {value: "present"}

                with self.assertRaises(AttributeError):
                    value.value = invalid
                with self.assertRaises(AttributeError):
                    value._value = invalid
                with self.assertRaises(AttributeError):
                    del value._value

                self.assertEqual(hash(value), original_hash)
                self.assertEqual(lookup[value], "present")

    def test_accepts_only_canonical_utc_whole_second_observation_time(self):
        record = self.build_evidence(observed_at="2026-08-14T08:30:00Z")

        self.assertEqual(record.observed_at, "2026-08-14T08:30:00Z")

    def test_rejects_ambiguous_or_non_canonical_observation_time(self):
        for invalid in (
            "2026-08-14",
            "2026-08-14T08:30:00",
            "2026-08-14T08:30:00+00:00",
            "2026-08-14T08:30:00.000Z",
            "2026-02-30T08:30:00Z",
        ):
            with self.subTest(invalid=invalid), self.assertRaises((TypeError, ValueError)):
                self.build_evidence(observed_at=invalid)


class EvidenceJsonContractTests(EvidenceCoreContractTests):
    def test_accepts_nested_json_compatible_metadata(self):
        record = self.build_evidence(
            metadata={
                "currency": "USD",
                "market": "US",
                "sample_size": 4,
                "nested": {"units": "items", "raw": [None, True, 1.5]},
            }
        )

        self.assertEqual(record.metadata["nested"]["raw"], [None, True, 1.5])

    def test_rejects_invalid_metadata(self):
        invalid_metadata = (
            [],
            {"": "empty key"},
            {"object": object()},
            {"not_finite": float("nan")},
            {"not_finite": float("inf")},
            {1: "non-string key"},
        )
        for metadata in invalid_metadata:
            with self.subTest(metadata=repr(metadata)), self.assertRaises((TypeError, ValueError)):
                self.build_evidence(metadata=metadata)

    def test_rejects_metadata_mutation_at_serialization_boundary(self):
        record = self.build_evidence(metadata={"nested": {"safe": 1}})
        record.metadata[""] = 1

        with self.assertRaises((TypeError, ValueError)):
            record.to_json()

    def test_rejects_corrupted_constrained_value_at_serialization_boundary(self):
        cases = (
            ("id", "bad-id"),
            ("tier", "Tier 5"),
            ("status", "observed"),
            ("confidence", "medium"),
        )
        for field, invalid in cases:
            with self.subTest(field=field):
                record = self.build_evidence()
                object.__setattr__(getattr(record, field), "_value", invalid)

                with self.assertRaises((TypeError, ValueError)):
                    record.to_json()

    def test_rejects_lone_surrogates_in_core_source_and_metadata_strings(self):
        surrogate = "\ud800"

        for field in ("claim", "evidence"):
            with self.subTest(field=field), self.assertRaises((TypeError, ValueError)):
                self.build_evidence(**{field: surrogate})

        for field in ("provider", "source_type", "reference", "title"):
            source_values = {
                "provider": "provider",
                "source_type": "document",
                "reference": "doc-1",
                "title": "title",
            }
            source_values[field] = surrogate
            with self.subTest(field=field), self.assertRaises((TypeError, ValueError)):
                self.module.Source(**source_values)

        for metadata in (
            {surrogate: 1},
            {"nested": {surrogate: 1}},
            {"nested": [surrogate]},
        ):
            with self.subTest(metadata=repr(metadata)), self.assertRaises((TypeError, ValueError)):
                self.build_evidence(metadata=metadata)

    def test_rejects_lone_surrogate_from_json_deserialization(self):
        payload = json.dumps(
            {
                "id": "E001",
                "claim": "\ud800",
                "evidence": "basis",
                "source": {
                    "provider": "provider",
                    "source_type": "document",
                    "reference": "doc-1",
                    "title": None,
                },
                "observed_at": "2026-08-14T08:30:00Z",
                "tier": "Tier 2",
                "status": "Observed",
                "confidence": "Medium",
                "metadata": {},
            }
        ).encode("utf-8")

        with self.assertRaises((TypeError, ValueError)):
            self.module.Evidence.from_json(payload)

    def test_serializes_with_fixed_field_order_and_utf8_json(self):
        record = self.build_evidence(
            claim='Quoted "fact" — café',
            evidence="Line one\nLine two",
            metadata={"z": 3, "nested": {"z": 0, "a": 1}, "a": 2},
        )

        serialized = record.to_json()
        expected = (
            '{"id":"E001","claim":"Quoted \\"fact\\" — café",'
            '"evidence":"Line one\\nLine two","source":{"provider":"Example Marketplace",'
            '"source_type":"marketplace_listing","reference":"https://example.test/products/123",'
            '"title":"Example product listing"},"observed_at":"2026-08-14T08:30:00Z",'
            '"tier":"Tier 2","status":"Observed","confidence":"Medium",'
            '"metadata":{"a":2,"nested":{"a":1,"z":0},"z":3}}'
        ).encode("utf-8")

        self.assertIsInstance(serialized, bytes)
        self.assertEqual(serialized, expected)

    def test_repeated_serialization_sorts_nested_metadata_deterministically(self):
        first = self.build_evidence(
            metadata={"z": 3, "nested": {"z": 0, "a": 1}, "a": 2}
        )
        second = self.build_evidence(
            metadata={"a": 2, "nested": {"a": 1, "z": 0}, "z": 3}
        )

        self.assertEqual(first.to_json(), first.to_json())
        self.assertEqual(first.to_json(), second.to_json())

    def test_deserializes_valid_json_into_typed_evidence(self):
        original = self.build_evidence(
            metadata={"nested": {"a": 1, "z": 2}, "raw": [False, None, 2.5]}
        )

        reconstructed = self.module.Evidence.from_json(original.to_json())

        self.assertEqual(reconstructed, original)
        self.assertIsInstance(reconstructed.id, self.module.EvidenceId)
        self.assertIsInstance(reconstructed.source, self.module.Source)
        self.assertIsInstance(reconstructed.tier, self.module.Tier)
        self.assertIsInstance(reconstructed.status, self.module.Status)
        self.assertIsInstance(reconstructed.confidence, self.module.Confidence)

    def test_rejects_malformed_or_non_finite_json(self):
        for payload in (b"{", b"not-json", b'{"id":NaN}'):
            with self.subTest(payload=payload), self.assertRaises((TypeError, ValueError)):
                self.module.Evidence.from_json(payload)

    def test_rejects_missing_extra_and_wrong_contract_fields_during_deserialization(self):
        valid = json.loads(self.build_evidence().to_json().decode("utf-8"))
        invalid_payloads = []

        missing = dict(valid)
        del missing["confidence"]
        invalid_payloads.append(("missing", missing))

        extra = dict(valid)
        extra["extra"] = "rejected"
        invalid_payloads.append(("extra", extra))

        wrong_source = dict(valid)
        wrong_source["source"] = "free-text"
        invalid_payloads.append(("wrong source", wrong_source))

        wrong_id = dict(valid)
        wrong_id["id"] = "E000"
        invalid_payloads.append(("wrong id", wrong_id))

        wrong_tier = dict(valid)
        wrong_tier["tier"] = 2
        invalid_payloads.append(("wrong tier", wrong_tier))

        wrong_status = dict(valid)
        wrong_status["status"] = "observed"
        invalid_payloads.append(("wrong status", wrong_status))

        wrong_confidence = dict(valid)
        wrong_confidence["confidence"] = "medium"
        invalid_payloads.append(("wrong confidence", wrong_confidence))

        wrong_time = dict(valid)
        wrong_time["observed_at"] = "2026-08-14"
        invalid_payloads.append(("wrong timestamp", wrong_time))

        wrong_metadata = dict(valid)
        wrong_metadata["metadata"] = []
        invalid_payloads.append(("wrong metadata", wrong_metadata))

        source_extra = dict(valid)
        source_extra["source"] = dict(valid["source"], extra="rejected")
        invalid_payloads.append(("extra source", source_extra))

        for name, payload in invalid_payloads:
            with self.subTest(name=name), self.assertRaises((TypeError, ValueError)):
                self.module.Evidence.from_json(json.dumps(payload).encode("utf-8"))

    def test_rejects_duplicate_json_fields(self):
        payload = (
            b'{"id":"E001","id":"E002","claim":"claim","evidence":"basis",'
            b'"source":{"provider":"provider","source_type":"document",'
            b'"reference":"doc-1","title":null},"observed_at":"2026-08-14T08:30:00Z",'
            b'"tier":"Tier 2","status":"Observed","confidence":"Medium","metadata":{}}'
        )

        with self.assertRaises((TypeError, ValueError)):
            self.module.Evidence.from_json(payload)

    def test_round_trip_reproduces_identical_canonical_bytes(self):
        original = self.build_evidence(
            metadata={"z": {"b": 2, "a": 1}, "a": ["x", 1.25, True]}
        )

        first = original.to_json()
        reconstructed = self.module.Evidence.from_json(first)
        second = reconstructed.to_json()

        self.assertEqual(reconstructed, original)
        self.assertEqual(second, first)


if __name__ == "__main__":
    unittest.main()
