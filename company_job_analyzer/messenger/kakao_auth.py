from __future__ import annotations

import os


def get_access_token() -> str | None:
    return os.getenv("KAKAO_ACCESS_TOKEN")

