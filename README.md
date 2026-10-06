# PowerLift-AI-X

**ML-powered powerlifting competition intelligence and planning platform**

PowerLift-AI-X combines real historical powerlifting competition data, a validated PDF-to-dataset pipeline, athlete identity resolution, temporal machine learning, and a Streamlit interface for competition planning.

## What it does

- Ingests historical powerlifting competition result sources
- Detects and parses multiple historical PDF layouts
- Validates and normalizes competition records
- Resolves athlete identities across competitions and years
- Builds temporal features without athlete leakage
- Predicts future squat, bench press, deadlift and total performance
- Provides competition planning and strategy workflows
- Exposes production logic through an API
- Presents the system through a Streamlit UI

## Architecture

```text
Historical Competition Sources
          ↓
PDF Discovery & Verification
          ↓
Extraction → Format Detection → Parsing
          ↓
Validation & Normalization
          ↓
Athlete Identity Resolution
          ↓
Canonical Competition Dataset
          ↓
Feature Engineering & Leakage Checks
          ↓
Machine Learning Models
          ↓
Prediction / Competition Intelligence
          ↓
FastAPI + Streamlit
```

## Main components

| Component | Purpose |
|---|---|
| `src/powerlift_ai_x/ingestion` | Source discovery and PDF ingestion |
| `src/powerlift_ai_x/parsing` | Multi-format result parsing |
| `src/powerlift_ai_x/normalization` | Canonical data normalization |
| `src/powerlift_ai_x/identity` | Athlete identity resolution |
| `src/powerlift_ai_x/dataset` | Dataset construction and audits |
| `src/powerlift_ai_x/ml` | Temporal features, leakage checks and model service |
| `src/powerlift_ai_x/api` | FastAPI backend |
| `app/` | Streamlit application and user workflows |
| `tests/` | Automated tests |
| `notebooks/` | EDA and ML experimentation |

## Machine Learning

The project uses historical athlete performance to create temporal features such as:

- Previous-year performance
- Historical mean / max / min totals
- Best squat, bench and deadlift
- Bodyweight history
- Performance-change features
- Years since previous competition

The production model artifacts are included where appropriate. Predictions are estimates and are **not guaranteed future competition results**.

## Data

The original project contains a large collection of competition PDFs and processed datasets. Those raw/processed datasets are intentionally excluded from this public GitHub package to keep the repository lightweight and avoid redistributing a large source-data collection.

The data pipeline scripts remain available so the workflow can be inspected and reproduced with appropriately sourced competition-result data.

## Local setup

### 1. Clone

```bash
git clone https://github.com/YOUR-USERNAME/PowerLift-AI-X.git
cd PowerLift-AI-X
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Streamlit app

```bash
streamlit run app/streamlit_app.py
```

### 5. Run tests

```bash
pytest
```

## Environment

Copy `.env.example` to `.env` if you need local configuration:

```bash
copy .env.example .env
```

Do **not** commit `.env` or API keys.

## Project status

**Version:** 0.1.0  
**Status:** Portfolio / development release

## Author

**Dhruv Karkera**  
BSc Data Science

---

If you find the project useful, feel free to ⭐ the repository.
