import json
from pathlib import Path

import pytest

from lib import vision
from lib.http import AppError

FIXTURES = Path(__file__).parent / "fixtures"


def fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


class FakeBedrock:
    """Minimal stand-in for the bedrock-runtime client's converse()."""

    def __init__(self, replies: list[str]):
        self.replies = list(replies)
        self.calls: list[dict] = []

    def converse(self, **kwargs):
        self.calls.append(kwargs)
        text = self.replies.pop(0)
        return {"output": {"message": {"role": "assistant", "content": [{"text": text}]}}}


def test_valid_json_parses():
    parsed = vision.parse_vision_text(fixture_text("mixed_bin.json"))
    assert parsed.isWasteImage is True
    assert parsed.segregationScore == 35
    assert len(parsed.items) == 5
    assert parsed.items[0].brand == "Bisleri"


def test_json_wrapped_in_prose_parses():
    parsed = vision.parse_vision_text(fixture_text("prose_wrapped.txt"))
    assert parsed.items[0].material == "CARDBOARD"
    assert parsed.segregationScore == 80


@pytest.mark.parametrize("text", ["no json here", "{not: valid json}", "", '{"items": []}'])
def test_invalid_json_raises_parse_error(text):
    with pytest.raises(vision.VisionParseError):
        vision.parse_vision_text(text)


def test_post_process_unknown_material_and_clamping():
    parsed = vision.parse_vision_text(fixture_text("odd_values.json"))
    items = vision.clean_items(parsed)
    blob, pile, speck = items
    assert blob["material"] == "OTHER_LANDFILL"
    assert blob["brand"] is None
    assert pile["material"] == "METAL"
    assert pile["estWeightKg"] == 10.0  # clamped max
    assert pile["count"] == 3
    assert pile["brand"] is None
    assert speck["estWeightKg"] == 0.005  # clamped min
    assert speck["count"] == 1
    assert parsed.segregationScore == 100


def test_analyze_happy_path_calls_converse_once_with_image():
    client = FakeBedrock([fixture_text("mixed_bin.json")])
    result = vision.analyze_image(b"\xff\xd8fake", "jpeg", client=client, model_id="test-model")
    assert len(client.calls) == 1
    call = client.calls[0]
    assert call["modelId"] == "test-model"
    assert call["inferenceConfig"] == {"temperature": 0.1, "maxTokens": 2000}
    content = call["messages"][0]["content"]
    assert content[0]["image"]["format"] == "jpeg"
    assert content[0]["image"]["source"]["bytes"] == b"\xff\xd8fake"
    assert content[1]["text"] == vision.PROMPT
    assert result["segregationScore"] == 35
    assert len(result["items"]) == 5
    assert result["tip"].startswith("Keep wet")


def test_analyze_retries_once_on_invalid_json():
    client = FakeBedrock(["I think it's a bin", fixture_text("mixed_bin.json")])
    result = vision.analyze_image(b"img", "png", client=client, model_id="m")
    assert len(client.calls) == 2
    assert vision.RETRY_LINE in client.calls[1]["messages"][0]["content"][1]["text"]
    assert len(result["items"]) == 5


def test_analyze_fails_after_second_invalid_reply():
    client = FakeBedrock(["nope", "still nope"])
    with pytest.raises(AppError) as exc:
        vision.analyze_image(b"img", "jpeg", client=client, model_id="m")
    assert exc.value.code == "AI_PARSE_FAILED"
    assert len(client.calls) == 2


def test_not_a_waste_image_raises_not_a_bin():
    client = FakeBedrock([fixture_text("not_a_bin.json")])
    with pytest.raises(AppError) as exc:
        vision.analyze_image(b"img", "jpeg", client=client, model_id="m")
    assert exc.value.code == "NOT_A_BIN"
    assert exc.value.status == 422


def test_waste_image_with_no_items_is_allowed():
    reply = json.dumps({"isWasteImage": True, "segregationScore": 50, "tip": "t", "items": []})
    result = vision.analyze_image(b"img", "jpeg", client=FakeBedrock([reply]), model_id="m")
    assert result["items"] == []


def test_image_format_from_key_and_content_type():
    assert vision.image_format("image/png", "scans/u/x.png") == "png"
    assert vision.image_format("image/jpeg", "scans/u/x.jpg") == "jpeg"
    assert vision.image_format(None, "scans/u/x.PNG") == "png"
    assert vision.image_format(None, "scans/u/x.bin") == "jpeg"
