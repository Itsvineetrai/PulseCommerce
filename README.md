# PulseCommerce Analytics Platform

> Product analytics, experimentation, churn intelligence, intervention optimization, and decision analytics in one end-to-end data platform.

PulseCommerce is an end-to-end analytics platform built around e-commerce behavioral event data. The platform transforms raw user events into warehouse analytics, A/B experiment analysis, churn-risk predictions, intervention recommendations, economic prioritization, and ROI-optimized intervention portfolios.

The project demonstrates how analytics engineering, machine learning, experimentation, decision systems, orchestration, validation, and dashboards can be integrated into a single reproducible workflow.

---

# Table of Contents

- [Project Overview](#project-overview)
- [Business Problem](#business-problem)
- [Platform Objectives](#platform-objectives)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Data Pipeline](#data-pipeline)
- [Behavioral Analytics](#behavioral-analytics)
- [Experimentation](#experimentation)
- [Churn Intelligence](#churn-intelligence)
- [Intervention Decision Engine](#intervention-decision-engine)
- [Intervention Economics and Portfolio Optimization](#intervention-economics-and-portfolio-optimization)
- [Pipeline Orchestration](#pipeline-orchestration)
- [Validation and Testing](#validation-and-testing)
- [Dashboard](#dashboard)
- [How to Run](#how-to-run)
- [Key Results](#key-results)
- [Future Improvements](#future-improvements)

---

# Project Overview

PulseCommerce converts raw e-commerce interaction events into actionable business intelligence.

The platform follows the complete analytical lifecycle:

```text
Raw Events
    ↓
Warehouse Loading
    ↓
Behavioral Analytics
    ↓
Experiment Population
    ↓
A/B Experiment Analysis
    ↓
Churn Feature Engineering
    ↓
Churn Model Training
    ↓
Churn Risk Scoring
    ↓
Intervention Candidate Generation
    ↓
Intervention Economics
    ↓
Portfolio Optimization
    ↓
ROI Analysis
    ↓
Dashboard and Decision Analytics

The final platform answers questions such as:

Where are customers dropping out of the funnel?
How does customer behavior change across sessions?
Did an experiment produce statistically significant improvement?
Which sessions have the highest churn risk?
Which customers should receive an intervention?
What intervention should be applied?
Which interventions generate the highest expected business value?
How should limited intervention capacity be allocated?
What is the expected ROI of the selected intervention portfolio?
Business Problem

E-commerce platforms generate large volumes of behavioral events, but raw events alone do not provide actionable decisions.

PulseCommerce addresses five connected analytical problems:

1. Behavioral Intelligence

Understand how users move through the e-commerce journey.

Examples:

Product View
    ↓
Add to Cart
    ↓
Cart View
    ↓
Checkout Start
    ↓
Payment Attempt
    ↓
Purchase Complete

The platform measures funnel progression, conversion performance, and behavioral velocity.

2. Experimentation

Determine whether product or business changes produce measurable improvements.

The platform:

Builds experiment populations
Calculates conversion rates
Measures absolute and relative lift
Performs a two-proportion Z-test
Performs a Chi-square consistency check
Calculates confidence intervals
Produces a statistical decision
3. Churn Intelligence

Identify sessions where customers are likely to leave without converting.

The system builds session-level features from observed behavior and uses a machine learning model to estimate churn probability.

4. Intervention Decisioning

Translate churn risk into business actions.

Examples include:

Cart recovery
Checkout recovery
Payment recovery
Monitoring
No action
5. Intervention Optimization

Intervention resources are limited.

Instead of targeting every eligible session, the system evaluates expected recovery value, intervention cost, and expected net value before selecting an optimized portfolio.

Platform Objectives

PulseCommerce was designed to:

Build a reproducible analytics warehouse
Analyze customer journey behavior
Measure funnel performance
Evaluate A/B experiments statistically
Create a churn prediction dataset
Train and persist a machine learning model
Score churn risk for all sessions
Generate intervention recommendations
Calculate intervention economics
Optimize interventions under capacity constraints
Calculate expected ROI
Orchestrate the workflow
Validate pipeline contracts
Present results through an interactive dashboard
Architecture
                         ┌─────────────────────────┐
                         │   Raw Event Data        │
                         │  E-commerce Events      │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌─────────────────────────┐
                         │   Warehouse Loader      │
                         │        DuckDB           │
                         └────────────┬────────────┘
                                      │
                                      ▼
                ┌──────────────────────────────────────┐
                │         Analytics Layer              │
                │                                      │
                │  • Session Funnel                    │
                │  • Funnel Metrics                    │
                │  • Velocity Metrics                  │
                └───────────────┬──────────────────────┘
                                │
                                ▼
                ┌──────────────────────────────────────┐
                │       Experimentation Layer          │
                │                                      │
                │  • Experiment Population            │
                │  • Conversion Analysis               │
                │  • Statistical Testing               │
                └───────────────┬──────────────────────┘
                                │
                                ▼
                ┌──────────────────────────────────────┐
                │        Churn Intelligence            │
                │                                      │
                │  • Feature Dataset                   │
                │  • Model Training                    │
                │  • Risk Scoring                      │
                └───────────────┬──────────────────────┘
                                │
                                ▼
                ┌──────────────────────────────────────┐
                │       Intervention Engine            │
                │                                      │
                │  • Candidate Generation             │
                │  • Economic Modeling                │
                │  • Portfolio Selection              │
                │  • ROI Analysis                     │
                └───────────────┬──────────────────────┘
                                │
                                ▼
                     ┌──────────────────────┐
                     │  Streamlit Dashboard │
                     └──────────────────────┘
Technology Stack
Programming and Analytics
Python 3.11+
SQL
Pandas
NumPy
Data Storage
DuckDB
PyArrow
Machine Learning
Scikit-learn
HistGradientBoostingClassifier
Statistical Analysis
SciPy
Orchestration
Prefect 3
Dashboard
Streamlit
Plotly
Testing and Quality
Pytest
Ruff
Project Structure
PulseCommerce/
│
├── dashboard/
│   ├── app.py
│   └── pages/
│       ├── 1_Executive_Overview.py
│       ├── 2_Funnel_and_Journey_Intelligence.py
│       ├── 3_Experimentation_Lab.py
│       ├── 4_Customer_Intelligence.py
│       └── 5_Intervention_Portfolio.py
│
├── data/
│   ├── landing/
│   ├── warehouse/
│   └── artifacts/
│
├── sql/
│   └── analytics/
│
├── scripts/
│   ├── load_warehouse.py
│   ├── run_analytics.py
│   ├── run_experiment_population.py
│   ├── run_experiment_analysis.py
│   ├── run_churn_feature_dataset.py
│   ├── train_final_churn_model.py
│   ├── score_churn_risk.py
│   ├── generate_intervention_candidates.py
│   ├── generate_intervention_economics.py
│   ├── generate_intervention_portfolio.py
│   ├── generate_intervention_roi.py
│   └── validation scripts
│
├── src/
│   └── pulsecommerce/
│       └── orchestration/
│           ├── __init__.py
│           └── pipeline_flow.py
│
├── tests/
│   └── test_orchestration.py
│
├── artifacts/
│   └── churn_model.joblib
│
├── pyproject.toml
└── README.md
Data Pipeline

The platform begins with raw e-commerce behavioral events.

Each event can contain information such as:

Event ID
User ID
Session ID
Event timestamp
Event name
Page
Device type
Traffic source
Product category
Quantity
Price
Cart value
Experiment variant
Event properties

The warehouse loading stage validates:

Duplicate event IDs
Missing required values
Invalid event names
Invalid experiment variants
Invalid timestamps

The validated events are loaded into the DuckDB warehouse.

Behavioral Analytics

The behavioral analytics layer produces three major warehouse outputs.

Session Funnel

Tracks how individual sessions progress through the customer journey.

Example stages:

Product View
    ↓
Add to Cart
    ↓
Cart View
    ↓
Checkout Start
    ↓
Payment Attempt
    ↓
Purchase Complete
Funnel Metrics

Aggregates funnel performance and conversion behavior.

The metrics help identify where customers abandon the journey.

Velocity Metrics

Measures behavioral timing and session movement.

This helps identify how quickly users move through important stages of the customer journey.

Experimentation

The experimentation pipeline evaluates control and treatment populations.

The analysis includes:

Conversion Rates
Conversion Rate =
Conversions / Total Users
Absolute Lift
Absolute Lift =
Treatment Conversion Rate
-
Control Conversion Rate
Relative Lift
Relative Lift =
(Treatment Rate - Control Rate)
/
Control Rate
Statistical Tests

The platform performs:

Two-Proportion Z-Test

Tests whether the conversion difference between control and treatment is statistically significant.

Chi-Square Consistency Check

Provides an additional statistical consistency check.

Confidence Interval

Calculates the uncertainty range around the conversion difference.

The output produces a decision:

Statistically Significant
        OR
No Statistically Significant Evidence
Churn Intelligence

The churn system converts event-level behavior into a session-level machine learning dataset.

Observation Cutoff

A key design principle is preventing label leakage.

For each session, the feature dataset uses behavioral information observed before the final outcome.

Purchase completion and terminal events are excluded from the observation window where necessary.

This prevents the model from learning the outcome directly from future events.

Features

Examples of session-level features include:

Total actions so far
Unique event types
Product views
Add-to-cart actions
Cart views
Checkout starts
Payment attempts
Payment errors
Cart presence
Checkout presence
Observed session duration
Device type
Traffic source
Churn Target
Purchased = 1
    ↓
Churned = 0

Purchased = 0
    ↓
Churned = 1
Machine Learning

The final churn model uses:

HistGradientBoostingClassifier

The trained model is persisted as:

artifacts/churn_model.joblib

The model is then used to score every session.

Churn Risk Scoring

Each session receives:

Churn Risk Score

The score is grouped into risk bands such as:

Low
Medium
High
Critical

This transforms model probabilities into interpretable business categories.

Intervention Decision Engine

The intervention engine converts risk scores and behavioral context into recommended actions.

Possible actions include:

no_action
monitor
cart_recovery
checkout_recovery
payment_recovery

The decision depends on:

Churn risk
Customer journey stage
Cart activity
Checkout behavior
Payment behavior
Business priority
Intervention Economics and Portfolio Optimization

Every intervention has an expected economic impact.

The system calculates:

Expected Recovery Value
Intervention Cost
Expected Net Value =
Expected Recovery Value
-
Intervention Cost
Portfolio Selection

Not every eligible customer can be contacted.

The platform therefore applies a capacity constraint.

Example:

Eligible Interventions
        ↓
Rank by Business Value
        ↓
Select Highest-Value Sessions
        ↓
Apply Capacity Limit

This creates an optimized intervention portfolio.

ROI Analysis

For each selected intervention:

ROI (%) =
(Expected Net Value / Intervention Cost) × 100

The platform provides:

Total expected recovered value
Total intervention cost
Total expected net value
Portfolio ROI
ROI by intervention action
Top ROI opportunities
Pipeline Orchestration

The entire platform is orchestrated using Prefect.

The pipeline executes stages in dependency order:

1. load_warehouse.py

2. run_analytics.py

3. run_experiment_population.py

4. run_experiment_analysis.py

5. run_churn_feature_dataset.py

6. train_final_churn_model.py

7. score_churn_risk.py

8. generate_intervention_candidates.py

9. generate_intervention_economics.py

10. generate_intervention_portfolio.py

11. generate_intervention_roi.py

Run the pipeline with:

python -m pulsecommerce.orchestration.pipeline_flow

The orchestration layer ensures the complete workflow can be executed as one reproducible process.

Validation and Testing

The project contains multiple validation layers.

Data Validation

Checks include:

Duplicate records
Missing values
Invalid event values
Invalid timestamps
ML Dataset Validation

Checks include:

Session counts
Duplicate sessions
Feature completeness
Target validity
Churn Risk Validation

Checks include:

Session reconciliation
Duplicate scores
Missing scored sessions
Unexpected sessions
Intervention Validation

Checks include:

Candidate reconciliation
Recommended action validity
Economics reconciliation
Portfolio capacity
Duplicate portfolio sessions
ROI Validation

Checks include:

Expected recovery values
Intervention costs
Net value formulas
ROI formulas
Portfolio reconciliation
End-to-End Pipeline Validation

The final validation contract verifies:

Warehouse Artifact
        ↓
Required Warehouse Tables
        ↓
Churn Feature Dataset
        ↓
Churn Risk Scores
        ↓
Intervention Candidates
        ↓
Intervention Economics
        ↓
Intervention Portfolio
        ↓
ROI Dataset

Run:

python scripts\validate_end_to_end_pipeline.py

Run the test suite:

pytest -q
Dashboard

The Streamlit dashboard provides an interactive interface for exploring the complete analytics platform.

Run:

streamlit run dashboard\app.py

The dashboard contains five major areas.

Executive Overview

Provides high-level platform KPIs and business metrics.

Funnel and Journey Intelligence

Explores customer movement through the funnel and behavioral journey.

Experimentation Lab

Presents experiment population, conversion performance, lift, statistical tests, and experiment decisions.

Customer Intelligence

Explores churn risk, customer behavior, and risk distribution.

Intervention Portfolio

Displays intervention recommendations, portfolio economics, expected recovery value, and ROI.

How to Run
1. Clone the Repository
git clone <your-repository-url>
cd PulseCommerce
2. Create a Virtual Environment
python -m venv .venv

Activate:

.venv\Scripts\Activate.ps1
3. Install the Project
pip install -e .

Install development dependencies:

pip install -e ".[dev]"
4. Run the Complete Pipeline
python -m pulsecommerce.orchestration.pipeline_flow
5. Validate the Pipeline
python scripts\validate_end_to_end_pipeline.py
6. Run Tests
pytest -q
7. Launch the Dashboard
streamlit run dashboard\app.py
Key Results

The final pipeline produced:

Data
Total raw events: 158,467
Total churn sessions: 15,000
Total users: 5,000
Churn Dataset
Churned sessions: 11,127
Converted sessions: 3,873
Churn rate: 74.18%
Churn Model
Model:
HistGradientBoostingClassifier
Intervention Portfolio
Portfolio capacity: 500 sessions
Selected sessions: 500
Portfolio Economics
Expected recovered value: 604,016.50
Total intervention cost: 2,500.00
Expected net value: 601,516.50
Expected ROI: 24,060.66%

These values represent model-based expected intervention economics rather than guaranteed realized business revenue.

Key Engineering Concepts Demonstrated

This project demonstrates:

Data validation
Analytics engineering
SQL transformations
Event-level to session-level modeling
Funnel analytics
Behavioral analytics
A/B testing
Statistical hypothesis testing
Confidence intervals
Machine learning feature engineering
Churn prediction
Model persistence
Risk scoring
Decision systems
Economic modeling
Portfolio optimization
ROI analysis
Workflow orchestration
Automated validation
Unit testing
Interactive analytics dashboards
Future Improvements

Potential production-level extensions include:

Data Platform
Incremental ingestion
Partitioned datasets
Data lineage
Schema contracts
Data quality monitoring
Machine Learning
Time-based validation
Probability calibration monitoring
Feature drift detection
Model performance monitoring
Model versioning
Intervention Engine
Uplift modeling
Causal treatment effect estimation
Dynamic intervention budgets
Multi-armed bandit experimentation
Feedback loops from realized interventions
Infrastructure
Containerization
CI/CD pipelines
Scheduled Prefect deployments
Cloud data warehouse integration
Centralized observability
Final Outcome

PulseCommerce is an integrated analytics platform that connects:

Customer Behavior
        ↓
Analytics
        ↓
Experimentation
        ↓
Machine Learning
        ↓
Risk Intelligence
        ↓
Business Decisions
        ↓
Economic Optimization
        ↓
Actionable Insights

The project moves beyond descriptive dashboards and demonstrates a complete path from raw behavioral data to optimized intervention decisions.

Author

Vineet Rai

Computer Science Engineering — Data Science