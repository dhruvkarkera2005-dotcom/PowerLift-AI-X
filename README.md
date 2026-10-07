# PowerLift-AI-X

**ML-powered powerlifting competition intelligence and planning platform**

PowerLift-AI-X combines historical powerlifting competition data, a validated PDF-to-dataset pipeline, athlete identity resolution, temporal machine learning, and an interactive Streamlit interface for performance analysis and competition planning.

## 🚀 What It Does

- Ingests historical powerlifting competition result sources
- Detects and parses multiple historical PDF layouts
- Validates and normalizes competition records
- Resolves athlete identities across competitions and years
- Builds temporal features while reducing athlete-data leakage
- Predicts squat, bench press, deadlift, and total performance
- Provides competition planning and strategy workflows
- Exposes backend functionality through FastAPI
- Provides an interactive Streamlit application

## 🏗️ Architecture

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
