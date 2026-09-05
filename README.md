# PulseCommerce — Product Analytics & Experimentation Platform

## Locked Architecture
Synthetic Event Generator → Event Landing (Parquet/JSONL) → Data Quality Layer → DuckDB Analytics Warehouse → Behavioral Analytics / Experiment Analytics / Customer Analytics → ML Feature Store → Abandonment Prediction → Intervention Engine → Prefect 3 Orchestration → Streamlit Dashboard.

This repository is intentionally analytics-first. Kafka, Spark, Airflow, Snowflake, dbt, APIs, RAG/LLM layers, and other infrastructure are NOT part of the baseline architecture unless a real requirement proves they are necessary.

## Business Questions
1. Where are we losing customers?
2. Why are we losing them?
3. Did a product change improve outcomes?
4. Who is likely to abandon?
5. Who should the business act on first?

## Phases
See `docs/PROJECT_PLAN.md` for the implementation sequence.

## Windows Quick Start
```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

The project is currently a scaffold. Implement phases in order.
