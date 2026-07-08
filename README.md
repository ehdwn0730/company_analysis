# Company Job Analyzer

채용공고 URL을 수집하고, HTML 본문에서 지원자격과 우대조건을 분류한 뒤 회사별 PDF를 생성하고 카카오톡 나에게 메시지로 PDF 링크를 전송하는 Python MVP입니다.

## 설치

```bash
pip install -r requirements.txt
```

## 1. 수동 URL 분석

`company_job_analyzer/data/job_urls.csv`에 공고 URL을 넣습니다.

```csv
company,job_title,keyword,url
관심회사,백엔드 개발자,Python,https://...
```

실행:

```bash
python -m company_job_analyzer.main --input company_job_analyzer/data/job_urls.csv --ignore-robots
```

기본 산출물은 PDF와 로그입니다.

```text
company_job_analyzer/output/회사명.pdf
company_job_analyzer/logs/run.log
```

## 2. 자동 URL 수집

회사와 직무 키워드 조합으로 검색 URL을 만들고, 검색 결과에서 채용공고로 보이는 링크를 수집합니다.

```bash
python -m company_job_analyzer.main ^
  --collect-urls ^
  --targets-csv company_job_analyzer/data/search_targets.csv ^
  --collect-only
```

결과는 기본적으로 `company_job_analyzer/data/collected_job_urls.csv`에 저장됩니다.

수집 후 바로 분석까지 실행:

```bash
python -m company_job_analyzer.main ^
  --collect-urls ^
  --targets-csv company_job_analyzer/data/search_targets.csv ^
  --ignore-robots
```

회사와 키워드를 CLI에서 직접 줄 수도 있습니다.

```bash
python -m company_job_analyzer.main ^
  --collect-urls ^
  --companies "카카오,네이버" ^
  --keywords "Python,데이터 엔지니어,백엔드" ^
  --collect-only
```

## 3. 중복 공고 제거

수동 CSV와 자동 수집 CSV 모두 분석 전에 URL 정규화와 중복 제거를 거칩니다.

제거 대상:

- URL fragment
- 마지막 `/`
- `utm_*`, `fbclid`, `gclid`, `ref`, `source` 같은 추적 파라미터
- 대소문자가 다른 동일 host

## 4. LLM 기반 항목 분류

기본은 rule-based 분류입니다. LLM을 켜면 전체 본문을 보고 `requirements`와 `preferences`를 JSON으로 분류합니다. LLM 호출이 실패하면 자동으로 rule-based 결과를 사용합니다.

```bash
set OPENAI_API_KEY=...
set LLM_MODEL=gpt-4.1-mini
python -m company_job_analyzer.main --input company_job_analyzer/data/job_urls.csv --use-llm --ignore-robots
```

OpenAI 호환 Chat Completions API를 쓰는 다른 엔드포인트는 아래처럼 바꿀 수 있습니다.

```bash
set LLM_ENDPOINT=https://api.openai.com/v1/chat/completions
set LLM_API_KEY=...
```

## 5. 카카오톡 전송

```bash
set KAKAO_ACCESS_TOKEN=...
set PUBLIC_DOWNLOAD_BASE_URL=https://your-download-host.example.com/reports
python -m company_job_analyzer.main --send-kakao --ignore-robots
```

`PUBLIC_DOWNLOAD_BASE_URL`이 없으면 로컬 `file://` 링크가 생성됩니다. 휴대폰 카카오톡에서 열려면 PDF가 웹에서 접근 가능한 위치에 있어야 합니다.

## 6. Airflow 스케줄링

Airflow 환경에서는 별도 의존성을 설치합니다.

```bash
pip install -r requirements-airflow.txt
```

DAG 파일:

```text
company_job_analyzer/airflow_dags/company_job_analyzer_dag.py
```

Airflow의 `dags_folder`에 이 파일을 복사하거나, 해당 폴더를 DAG 경로로 잡습니다.

주요 환경변수:

```bash
set COMPANY_JOB_ANALYZER_PROJECT_DIR=C:\Users\ehdwn\Desktop\project\research_company
set AIRFLOW_JOB_ANALYZER_INPUT=C:\Users\ehdwn\Desktop\project\research_company\company_job_analyzer\data\job_urls.csv
set AIRFLOW_JOB_ANALYZER_USE_LLM=true
set AIRFLOW_JOB_ANALYZER_SEND_KAKAO=false
set AIRFLOW_JOB_ANALYZER_IGNORE_ROBOTS=true
```

기본 스케줄은 매일 1회(`@daily`)입니다.

## 산출물

```text
company_job_analyzer/output/
└── 회사명.pdf
```

로그:

```text
company_job_analyzer/logs/run.log
```
