"""Bin Vision: Amazon Bedrock Converse (Amazon Nova Lite) image analysis (spec section 10.1).

The model only describes what it sees. Weights are clamped and categories/money are computed in code.
"""
import json
import logging
from typing import Any, Optional

from pydantic import ValidationError

from lib import config
from lib.http import AppError
from lib.materials import normalize_material
from lib.models import VisionResponse

logger = logging.getLogger()

PROMPT = """You are a waste-audit assistant for households in Delhi, India.
Look at the photo of a household dustbin or pile of discarded items.

Identify each distinct item or group of similar items you can see. For each, estimate:
- material: one of PET_BOTTLE, HARD_PLASTIC, MILK_POUCH, MULTILAYER_PACKET, PAPER, CARDBOARD, METAL, GLASS, E_WASTE, WET_ORGANIC, SANITARY, OTHER_LANDFILL
- count: number of items (integer; 1 for loose material like food scraps)
- estWeightKg: your best estimate of total weight in kilograms for that group
- brand: the brand name if clearly readable on packaging (e.g. "Amul", "Lay's"), otherwise null. Never guess a brand you cannot read.

Also assess:
- isWasteImage: true if the photo shows waste/discarded items, false otherwise
- segregationScore: 0-100. 100 = dry and wet waste fully separated; 0 = everything mixed and contaminated
- tip: one short, practical sentence (max 20 words) on what this household could do better, specific to what you see

Rules:
- Only list items you can actually see. Do not invent items.
- Be conservative with weights. Typical: empty PET bottle 0.02-0.04 kg, chips packet 0.005-0.01 kg, milk pouch 0.005 kg, newspaper sheet 0.02 kg, cardboard box 0.1-0.4 kg.
- Respond with JSON only, no other text, matching exactly:
{"isWasteImage": bool, "segregationScore": int, "tip": string,
 "items": [{"name": string, "material": string, "count": int, "estWeightKg": number, "brand": string|null}]}"""

RETRY_LINE = "Your previous reply was not valid JSON. Reply with JSON only."

MIN_ITEM_KG = 0.005
MAX_ITEM_KG = 10.0
TEMPERATURE = 0.1
MAX_TOKENS = 2000


class VisionParseError(ValueError):
    pass


def parse_vision_text(text: str) -> VisionResponse:
    """Take the substring from the first '{' to the last '}', parse and validate it."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        raise VisionParseError("no JSON object in model reply")
    try:
        return VisionResponse.model_validate(json.loads(text[start : end + 1]))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise VisionParseError(str(exc)) from exc


def clean_items(parsed: VisionResponse) -> list[dict]:
    """Post-process in code: clamp weights, map unknown materials to OTHER_LANDFILL."""
    cleaned = []
    for it in parsed.items:
        weight = min(MAX_ITEM_KG, max(MIN_ITEM_KG, it.estWeightKg))
        cleaned.append(
            {
                "name": it.name,
                "material": normalize_material(it.material).value,
                "count": it.count,
                "estWeightKg": round(weight, 3),
                "brand": it.brand,
            }
        )
    return cleaned


def image_format(content_type: Optional[str], key: str) -> str:
    if (content_type or "").lower() == "image/png" or key.lower().endswith(".png"):
        return "png"
    return "jpeg"


def _bedrock_client() -> Any:
    import boto3

    return boto3.client("bedrock-runtime", region_name=config.aws_region())


def _converse_text(client: Any, model_id: str, image: bytes, fmt: str, prompt: str) -> str:
    response = client.converse(
        modelId=model_id,
        messages=[
            {
                "role": "user",
                "content": [
                    {"image": {"format": fmt, "source": {"bytes": image}}},
                    {"text": prompt},
                ],
            }
        ],
        inferenceConfig={"temperature": TEMPERATURE, "maxTokens": MAX_TOKENS},
    )
    blocks = response.get("output", {}).get("message", {}).get("content", [])
    return "".join(b.get("text", "") for b in blocks)


def analyze_image(image: bytes, fmt: str, client: Any = None, model_id: Optional[str] = None) -> dict:
    """Run the vision model, retrying once on unparseable output.

    Returns {"items": [...], "segregationScore": int, "tip": str}.
    Raises AppError AI_PARSE_FAILED or NOT_A_BIN.
    """
    client = client or _bedrock_client()
    model_id = model_id or config.model_id()

    parsed: Optional[VisionResponse] = None
    for prompt in (PROMPT, f"{PROMPT}\n\n{RETRY_LINE}"):
        text = _converse_text(client, model_id, image, fmt, prompt)
        try:
            parsed = parse_vision_text(text)
            break
        except VisionParseError as exc:
            logger.warning("vision_parse_failed err=%s reply_head=%r", exc, text[:200])

    if parsed is None:
        raise AppError("AI_PARSE_FAILED", "The AI couldn't read this photo clearly. Please try another photo.", 502)
    if not parsed.isWasteImage:
        raise AppError(
            "NOT_A_BIN",
            "This doesn't look like a dustbin or waste. Try a photo of your bin or the items you're throwing away.",
            422,
        )
    return {"items": clean_items(parsed), "segregationScore": parsed.segregationScore, "tip": parsed.tip}
