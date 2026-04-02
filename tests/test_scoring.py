"""Tests for scoring functions."""

from soma_evals.scoring import flatten_yaml_to_slots, score_sets, score_slots, score_values


class TestScoreSets:
    def test_both_empty(self) -> None:
        result = score_sets(set(), set())
        assert result["precision"] == 1.0
        assert result["recall"] == 1.0
        assert result["f1"] == 1.0

    def test_perfect_match(self) -> None:
        result = score_sets({"a", "b", "c"}, {"a", "b", "c"})
        assert result["precision"] == 1.0
        assert result["recall"] == 1.0
        assert result["f1"] == 1.0
        assert result["false_positives"] == []
        assert result["false_negatives"] == []

    def test_partial_overlap(self) -> None:
        result = score_sets({"a", "b", "d"}, {"a", "b", "c"})
        assert result["precision"] == round(2 / 3, 4)
        assert result["recall"] == round(2 / 3, 4)
        assert result["false_positives"] == ["d"]
        assert result["false_negatives"] == ["c"]

    def test_no_overlap(self) -> None:
        result = score_sets({"x", "y"}, {"a", "b"})
        assert result["precision"] == 0.0
        assert result["recall"] == 0.0
        assert result["f1"] == 0.0

    def test_predicted_empty(self) -> None:
        result = score_sets(set(), {"a", "b"})
        assert result["precision"] == 0.0
        assert result["recall"] == 0.0

    def test_expected_empty(self) -> None:
        result = score_sets({"a", "b"}, set())
        assert result["recall"] == 0.0


class TestScoreSlots:
    def test_dict_keys_compared(self) -> None:
        predicted = {"name": "foo", "id": "123"}
        expected = {"name": "bar", "id": "456", "description": "baz"}
        result = score_slots(predicted, expected)
        assert result["precision"] == 1.0  # 2/2
        assert result["recall"] == round(2 / 3, 4)  # 2/3


class TestScoreValues:
    def test_exact_match(self) -> None:
        predicted = {"name": "foo", "id": "123"}
        expected = {"name": "foo", "id": "123"}
        result = score_values(predicted, expected)
        assert result["exact_matches"] == 2
        assert result["accuracy"] == 1.0

    def test_partial_match(self) -> None:
        predicted = {"name": "foo", "id": "999"}
        expected = {"name": "foo", "id": "123"}
        result = score_values(predicted, expected)
        assert result["exact_matches"] == 1
        assert result["accuracy"] == 0.5

    def test_case_insensitive_normalization(self) -> None:
        predicted = {"name": "  FOO  "}
        expected = {"name": "foo"}
        result = score_values(predicted, expected)
        assert result["exact_matches"] == 1

    def test_no_common_slots(self) -> None:
        result = score_values({"a": 1}, {"b": 2})
        assert result["total_compared"] == 0
        assert result["accuracy"] == 0.0


class TestFlattenYaml:
    def test_flat_dict(self) -> None:
        data = {"name": "foo", "id": "123"}
        result = flatten_yaml_to_slots(data)
        assert result == {"name": "foo", "id": "123"}

    def test_nested_dict(self) -> None:
        data = {"subject": {"name": "bar", "species": {"id": "NCBITaxon:9606"}}}
        result = flatten_yaml_to_slots(data)
        assert result["subject.name"] == "bar"
        assert result["subject.species.id"] == "NCBITaxon:9606"

    def test_list_of_dicts(self) -> None:
        data = {"items": [{"id": "1"}, {"id": "2"}]}
        result = flatten_yaml_to_slots(data)
        assert result["items[0].id"] == "1"
        assert result["items[1].id"] == "2"

    def test_list_of_scalars(self) -> None:
        data = {"tags": ["a", "b"]}
        result = flatten_yaml_to_slots(data)
        assert result["tags[0]"] == "a"
        assert result["tags[1]"] == "b"
