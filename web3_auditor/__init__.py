from __future__ import annotations

import os
import sys

GEMINI_API_KEY_PLACEHOLDER = "your-gemini-api-key-here"


def validate_config() -> None:
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key or key.strip() == GEMINI_API_KEY_PLACEHOLDER:
        print(
            "FATAL: GEMINI_API_KEY is not set or is still the placeholder value.\n"
            "Copy .env.example to .env and set a valid Gemini API key.",
            file=sys.stderr,
        )
        sys.exit(1)
