import pytest
from cmm.codex_llm import extract_json


def test_extract_json_plain():
    assert extract_json('{"themes": [1, 2]}') == {"themes": [1, 2]}


def test_extract_json_with_fence_and_prose():
    raw = 'Here is the result:\n```json\n{"a": 1}\n```\nDone.'
    assert extract_json(raw) == {"a": 1}


def test_extract_json_embedded_array():
    assert extract_json('prose [{"x": 1}] trailing') == [{"x": 1}]


def test_extract_json_raises_on_garbage():
    with pytest.raises(ValueError, match="no JSON"):
        extract_json("there is nothing parseable here")
