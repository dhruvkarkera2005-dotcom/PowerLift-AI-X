# PowerLift-AI-X

**ML-powered powerlifting competition intelligence and planning platform**

PowerLift-AI-X combines historical powerlifting competition data, a validated PDF-to-dataset pipeline, athlete identity resolution, temporal machine learning, and an interactive Streamlit interface for performance analysis and competition planning.

##  What It Does

- Ingests historical powerlifting competition result sources
- Detects and parses multiple historical PDF layouts
- Validates and normalizes competition records
- Resolves athlete identities across competitions and years
- Builds temporal features while reducing athlete-data leakage
- Predicts squat, bench press, deadlift, and total performance
- Provides competition planning and strategy workflows
- Exposes backend functionality through FastAPI
- Provides an interactive Streamlit application

##  Architecture

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

##  Main Components

| Component | Purpose |
|---|---|
| `src/powerlift_ai_x/ingestion` | Source discovery and PDF ingestion |
| `src/powerlift_ai_x/parsing` | Multi-format competition result parsing |
| `src/powerlift_ai_x/normalization` | Canonical data normalization |
| `src/powerlift_ai_x/identity` | Athlete identity resolution |
| `src/powerlift_ai_x/dataset` | Dataset construction and validation audits |
| `src/powerlift_ai_x/ml` | Temporal features, leakage checks and model services |
| `src/powerlift_ai_x/api` | FastAPI backend |
| `app/` | Streamlit application and user workflows |
| `tests/` | Automated tests |
| `notebooks/` | EDA and ML experimentation |

##  Machine Learning

The system uses historical athlete performance to construct temporal features such as:

- Previous competition performance
- Previous-year performance
- Historical mean, maximum and minimum totals
- Best squat, bench press and deadlift
- Bodyweight history
- Performance-change features
- Years since previous competition

These features are used to estimate future competition performance.

> **Note:** Model predictions are estimates and are not guaranteed future competition results.

##  Data Engineering Pipeline

The data engineering pipeline handles:

1. Competition source discovery
2. PDF verification
3. PDF format detection
4. Structured result extraction
5. Data validation
6. Field normalization
7. Athlete identity resolution
8. Dataset construction
9. Quality checks
10. ML-ready feature generation

This converts competition results from different historical document formats into a consistent analytical dataset.

##  Application

The Streamlit interface provides workflows for:

- Competition planning
- Athlete performance analysis
- Competition outlook
- Game-plan generation
- AI-assisted coaching insights
- Historical performance exploration

FastAPI provides the backend API layer for production-oriented application logic.



##  Tech Stack

### Programming & Data
- Python
- Pandas
- NumPy
- Scikit-learn

### Machine Learning
- Scikit-learn
- XGBoost
- LightGBM
- CatBoost

### Backend
- FastAPI
- Pydantic
- Uvicorn

### Frontend & Visualization
- Streamlit
- Plotly

### Data Engineering
- PDF parsing
- Web scraping
- Data validation
- Data normalization
- Feature engineering

### Development
- Git
- GitHub
- Pytest
- Jupyter

##  Data

The original project contains a large collection of competition PDFs and processed datasets.

Raw and processed datasets are intentionally excluded from this public repository to:

- Keep the repository lightweight
- Avoid redistributing a large source-data collection
- Keep the repository focused on the reproducible software pipeline

The data-processing and ML pipeline code remains available so the workflow can be inspected and reproduced with appropriately sourced competition-result data.

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/dhruvkarkera2005-dotcom/PowerLift-AI-X.git
cd PowerLift-AI-X
python -m venv .venv
.venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env
streamlit run app/streamlit_app.py
pytest

Environment
Configuration is provided through .env.example.
Sensitive configuration such as API keys, database credentials and access tokens should remain in .env and must never be committed to GitHub.
 Project Status
Version: 0.1.0
Status: Portfolio / Development Release
 Author
Dhruv Karkera
BSc Data Science
