from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT_DIR.parent


@dataclass(frozen=True)
class Settings:
    project_dir: Path = PROJECT_DIR
    data_dir: Path = ROOT_DIR / "data"
    output_dir: Path = ROOT_DIR / "output"
    log_dir: Path = ROOT_DIR / "logs"
    sites_yaml: Path = ROOT_DIR / "config" / "sites.yaml"
    user_agent: str = os.getenv(
        "JOB_ANALYZER_USER_AGENT",
        "CompanyJobAnalyzerMVP/0.1 (+https://example.local)",
    )
    request_timeout_sec: int = int(os.getenv("JOB_ANALYZER_TIMEOUT_SEC", "15"))
    request_retry_count: int = int(os.getenv("JOB_ANALYZER_RETRY_COUNT", "2"))
    search_result_limit: int = int(os.getenv("JOB_ANALYZER_SEARCH_RESULT_LIMIT", "20"))
    public_download_base_url: str | None = os.getenv("PUBLIC_DOWNLOAD_BASE_URL")
    kakao_access_token: str | None = os.getenv("KAKAO_ACCESS_TOKEN")
    send_kakao: bool = os.getenv("SEND_KAKAO", "false").lower() == "true"
    llm_provider: str = os.getenv("LLM_PROVIDER", "openai")
    llm_api_key: str | None = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4.1-mini")
    llm_endpoint: str = os.getenv("LLM_ENDPOINT", "https://api.openai.com/v1/chat/completions")
    llm_timeout_sec: int = int(os.getenv("LLM_TIMEOUT_SEC", "30"))
    airflow_input_csv: str = os.getenv("AIRFLOW_JOB_ANALYZER_INPUT", str(ROOT_DIR / "data" / "job_urls.csv"))

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
