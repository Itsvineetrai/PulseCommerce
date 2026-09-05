# Locked Architecture

```text
Synthetic Event Generator
        |
        v
Event Landing (Parquet / JSONL)
        |
        v
Data Quality Layer
        |
        v
DuckDB Analytics Warehouse
        |
   +----+-----+------+
   |          |      |
   v          v      v
Behavioral  Experiment Customer
Analytics   Analytics  Analytics
   \          |       /
    \         |      /
        ML Feature Layer
               |
               v
      Abandonment Prediction
               |
               v
      Intervention Intelligence
               |
               v
       Prefect Orchestration
               |
               v
       Streamlit Analytics Console
```

## Non-duplication rule
Each responsibility has one primary module. Extend that module before creating another pipeline, table, or service.
