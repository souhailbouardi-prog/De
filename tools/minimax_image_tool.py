"""
MiniMax Image Generation Tool

Generates images from text prompts using MiniMax's image-01 model via their REST API.
Returns a base64-decoded image saved to a temp file and served as a URL, or the raw
base64 data depending on response_format.

Requires: MINIMAX_API_KEY environment variable.
"""

import base64
import datetime
import json
import logging
import os
import tempfile
import uuid

import requests

from tools.debug_helpers import DebugSession

logger = logging.getLogger(__name__)

MINIMAX_IMAGE_API_URL = "https://api.minimax.io/v1/image_generation"
MINIMAX_IMAGE_MODEL = "image-01"

# Aspect ratio mapping — simplified choices for model to select
MINIMAX_ASPECT_RATIO_MAP = {
    "landscape": "16:9",
    "square": "1:1",
    "portrait": "9:16",
}

_debug = DebugSession("minimax_image_tools", env_var="MINIMAX_IMAGE_DEBUG")


def _get_minimax_api_key() -> str | None:
    """Return the MiniMax API key from environment variables."""
    return os.getenv("MINIMAX_API_KEY")


def minimax_image_generate_tool(
    prompt: str,
    aspect_ratio: str = "landscape",
) -> str:
    """
    Generate an image from a text prompt using MiniMax image-01.

    Args:
        prompt: The text prompt describing the desired image.
        aspect_ratio: "landscape", "square", or "portrait".

    Returns:
        JSON string with {"success": bool, "image": str|None}.
    """
    debug_call_data = {
        "parameters": {"prompt": prompt, "aspect_ratio": aspect_ratio},
        "error": None,
        "success": False,
        "generation_time": 0,
    }

    start_time = datetime.datetime.now()

    try:
        if not prompt or not isinstance(prompt, str) or not prompt.strip():
            raise ValueError("Prompt is required and must be a non-empty string")

        api_key = _get_minimax_api_key()
        if not api_key:
            raise ValueError("MINIMAX_API_KEY environment variable not set")

        # Resolve aspect ratio
        ar_lower = aspect_ratio.lower().strip() if aspect_ratio else "landscape"
        if ar_lower not in MINIMAX_ASPECT_RATIO_MAP:
            logger.warning("Invalid aspect_ratio '%s', defaulting to 'landscape'", aspect_ratio)
            ar_lower = "landscape"
        resolved_ar = MINIMAX_ASPECT_RATIO_MAP[ar_lower]

        logger.info("Generating image with MiniMax image-01: %s", prompt[:80])

        payload = {
            "model": MINIMAX_IMAGE_MODEL,
            "prompt": prompt.strip(),
            "aspect_ratio": resolved_ar,
            "response_format": "url",
        }

        headers = {"Authorization": f"Bearer {api_key}"}

        resp = requests.post(
            MINIMAX_IMAGE_API_URL,
            headers=headers,
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        data = resp.json()

        generation_time = (datetime.datetime.now() - start_time).total_seconds()

        # Handle url response format
        if "data" in data and "image_urls" in data["data"]:
            urls = data["data"]["image_urls"]
            if not urls:
                raise ValueError("No image URLs returned from MiniMax API")
            image_url = urls[0]
        elif "data" in data and "image_base64" in data["data"]:
            # Fallback: if server returns base64 despite requesting url
            images_b64 = data["data"]["image_base64"]
            if not images_b64:
                raise ValueError("No images returned from MiniMax API")
            # Write to temp file and return a file:// path
            raw = base64.b64decode(images_b64[0])
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            tmp.write(raw)
            tmp.close()
            image_url = f"file://{tmp.name}"
        else:
            raise ValueError(f"Unexpected response structure from MiniMax API: {list(data.keys())}")

        logger.info("MiniMax image generated in %.1fs", generation_time)

        response_data = {"success": True, "image": image_url}

        debug_call_data["success"] = True
        debug_call_data["generation_time"] = generation_time
        _debug.log_call("minimax_image_generate", debug_call_data)
        _debug.save()

        return json.dumps(response_data, indent=2, ensure_ascii=False)

    except Exception as e:
        generation_time = (datetime.datetime.now() - start_time).total_seconds()
        error_msg = f"Error generating image via MiniMax: {e}"
        logger.error("%s", error_msg, exc_info=True)

        response_data = {
            "success": False,
            "image": None,
            "error": str(e),
            "error_type": type(e).__name__,
        }

        debug_call_data["error"] = error_msg
        debug_call_data["generation_time"] = generation_time
        _debug.log_call("minimax_image_generate", debug_call_data)
        _debug.save()

        return json.dumps(response_data, indent=2, ensure_ascii=False)


def check_minimax_image_requirements() -> bool:
    """Check if MiniMax image generation requirements are met."""
    return bool(_get_minimax_api_key())


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
from tools.registry import registry, tool_error  # noqa: E402

MINIMAX_IMAGE_GENERATE_SCHEMA = {
    "name": "minimax_image_generate",
    "description": (
        "Generate high-quality images from text prompts using MiniMax image-01 model. "
        "Returns a single image URL. Display it using markdown: ![description](URL)"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "The text prompt describing the desired image. Be detailed and descriptive.",
            },
            "aspect_ratio": {
                "type": "string",
                "enum": ["landscape", "square", "portrait"],
                "description": (
                    "The aspect ratio of the generated image. "
                    "'landscape' is 16:9 wide, 'portrait' is 9:16 tall, 'square' is 1:1."
                ),
                "default": "landscape",
            },
        },
        "required": ["prompt"],
    },
}


def _handle_minimax_image_generate(args, **kw):
    prompt = args.get("prompt", "")
    if not prompt:
        return tool_error("prompt is required for image generation")
    return minimax_image_generate_tool(
        prompt=prompt,
        aspect_ratio=args.get("aspect_ratio", "landscape"),
    )


registry.register(
    name="minimax_image_generate",
    toolset="image_gen",
    schema=MINIMAX_IMAGE_GENERATE_SCHEMA,
    handler=_handle_minimax_image_generate,
    check_fn=check_minimax_image_requirements,
    requires_env=["MINIMAX_API_KEY"],
    is_async=False,
    emoji="🎨",
)
