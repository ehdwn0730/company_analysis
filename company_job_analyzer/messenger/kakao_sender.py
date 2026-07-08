from __future__ import annotations

import json

import requests


KAKAO_MEMO_URL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"


class KakaoSendError(RuntimeError):
    pass


def send_pdf_link_to_me(access_token: str, company: str, download_link: str) -> None:
    template_object = {
        "object_type": "text",
        "text": f"{company} 채용공고 분석 PDF가 생성되었습니다.\n{download_link}",
        "link": {"web_url": download_link, "mobile_web_url": download_link},
        "button_title": "PDF 열기",
    }
    response = requests.post(
        KAKAO_MEMO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        data={"template_object": json.dumps(template_object, ensure_ascii=False)},
        timeout=10,
    )
    if response.status_code >= 400:
        raise KakaoSendError(f"Kakao send failed: {response.status_code} {response.text}")

