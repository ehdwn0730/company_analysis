from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator


PROJECT_DIR = Path(os.getenv("COMPANY_JOB_ANALYZER_PROJECT_DIR", Path(__file__).resolve().parents[2]))
INPUT_CSV = os.getenv("AIRFLOW_JOB_ANALYZER_INPUT")


def run_company_job_analyzer() -> None:
    command = [
        sys.executable,
        "-m",
        "company_job_analyzer.main",
    ]
    if INPUT_CSV:
        command.extend(["--input", INPUT_CSV])
    if os.getenv("AIRFLOW_JOB_ANALYZER_SEND_KAKAO", "false").lower() == "true":
        command.append("--send-kakao")
    if os.getenv("AIRFLOW_JOB_ANALYZER_USE_LLM", "false").lower() == "true":
        command.append("--use-llm")
    if os.getenv("AIRFLOW_JOB_ANALYZER_IGNORE_ROBOTS", "false").lower() == "true":
        command.append("--ignore-robots")
    subprocess.run(command, cwd=str(PROJECT_DIR), check=True)


with DAG(
    dag_id="company_job_analyzer_daily",
    description="Collect and analyze company job postings, then generate company reports.",
    start_date=datetime(2026, 1, 1),
    schedule="@daily",
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=5)},
    tags=["job", "company-analysis"],
) as dag:
    PythonOperator(
        task_id="run_company_job_analyzer",
        python_callable=run_company_job_analyzer,
    )
