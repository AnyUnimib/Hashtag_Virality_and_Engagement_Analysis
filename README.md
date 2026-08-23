# Hashtag Virality and Engagement Analysis

### A FastAPI + MongoDB Pipeline for Social Media Data Integration

![Python](https://img.shields.io/badge/Python-3.10-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-async-009688?logo=fastapi&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB-Motor-47A248?logo=mongodb&logoColor=white)
![Status](https://img.shields.io/badge/status-completed-brightgreen)

**Data Management** · Università degli Studi di Milano-Bicocca · A.Y. 2024–2025

An asynchronous data integration pipeline that combines real-time Instagram data with historical Kaggle data to study what makes social media hashtags go viral — built as a FastAPI service backed by MongoDB.

---

## Table of Contents

- [Overview](#overview)
- [Data Sources](#data-sources)
- [Architecture](#architecture)
- [Data Integration & Quality](#data-integration--quality)
- [Key Findings](#key-findings)
- [API Endpoints](#api-endpoints)
- [Repository Contents](#repository-contents)
- [Setup & Usage](#setup--usage)
- [Tech Stack](#tech-stack)
- [Authors](#authors)

---

## Overview

Not all hashtags go viral — some drive massive engagement while others go unnoticed. This project builds a data pipeline to study *why*, focusing on four sectors: **Tourism & Travel, Cultural & Heritage, Food & Hospitality, and Wellness & Spirituality**. It integrates a real-time Instagram feed with historical engagement data into a single MongoDB-backed system, exposed through a FastAPI service for querying and analysis.

| Research Question | Approach |
|---|---|
| Which hashtags drive the most engagement? | Aggregate & rank by engagement score across sources |
| How does hashtag usage differ by industry? | Keyword-based category mapping into 4 sectors |

---

## Data Sources

| Source | Type | Description |
|---|---|---|
| **Instagram (Apify API)** | Real-time | Posts tracked by industry-specific hashtags — likes, shares, replies, timestamps |
| **Kaggle** | Historical | Structured engagement dataset used for comparative, longitudinal analysis |

Both sources were normalized into a common schema (hashtags, engagement metrics, timestamps) and merged using a hash-based unique identifier built from timestamp + post content + hashtags.

---

## Architecture

The system follows a modular, microservices-inspired design with three components:

1. **Data Collection Module** — retrieves data from the Apify API (Instagram) and Kaggle CSVs
2. **Processing & Storage Module** — cleans, integrates, and persists data to MongoDB
3. **API Layer** — FastAPI endpoints for querying, filtering, and analyzing the integrated dataset

Data is organized into three MongoDB collections:

| Collection | Contents |
|---|---|
| `collection_social_media_api` | Raw real-time posts from the Apify/Instagram API |
| `collection_social_media_csv` | Historical data imported from Kaggle |
| `collection_social_media_filtered_csv` | Cleaned & enriched data — extracted hashtags, computed engagement scores |

---

## Data Integration & Quality

**Preprocessing pipeline:**
- Missing values handled via Pandas (`df.replace({np.nan: None})`)
- Timestamps standardized with `pd.to_datetime`
- Hashtags normalized via regex, duplicates removed via hash-based filtering
- Cross-source entity matching via **TF-IDF + Cosine Similarity**

**Engineered features:**
- `Engagement Score = likes + shares + replies + hashtag count`
- Hashtags mapped to 4 industry categories (Tourism, Food, Cultural, Wellness) via keyword matching

**Measured quality improvement after integration:**

| Metric | Before | After |
|---|---|---|
| Missing values | 12% | 1.5% |
| Duplicate records | 5% | 0% |
| Data consistency | Moderate | High |
| Timestamp alignment | Inconsistent | Aligned |

---

## Key Findings

- **Tourism dominates engagement** — 725,943 total engagements, far ahead of Travel (90,540), Food (11,760), Cultural (11,076), and Wellness (2,054).
- **Specificity beats generality:** region-specific hashtags like `#BiharTourism` (10,791 engagements) and `#BlissfulBihar` (9,963) massively outperformed generic ones like `#Bihar` (2,913) and `#BiharKiShaan` (2,774).
- **Niche ≠ low value:** Wellness hashtags (`#yoga`, `#meditation`) had the lowest raw volume but maintained a small, consistently engaged audience — different sectors call for different strategies, not just "go viral" tactics.
- **Timing matters:** hashtags tied to cultural events and seasonal moments (e.g. `#diwali`, `#summervacation`) spiked sharply during their relevant windows.

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/get-api-data` | GET | Fetch live data directly from the Instagram/Apify API (no storage) |
| `/save-api-data` | POST | Fetch & store new data from the Instagram/Apify API |
| `/save-csv-data` | POST | Load and store the Kaggle CSV dataset (background task) |
| `/save-filtered-csv-data` | POST | Load, clean & store the enriched CSV dataset (background task) |
| `/make-integration` | POST | Merge API + CSV data into the integrated/filtered collection |
| `/get-saved-api-data` | GET | Retrieve stored API data (paginated) |
| `/get-saved-csv-data` | GET | Retrieve stored CSV data (paginated) |
| `/get-integrated-data` | GET | Retrieve the merged/integrated dataset (paginated) |
| `/delete-all-api-data/` | DELETE | Clear all stored API data |
| `/delete-all-csv-data/` | DELETE | Clear all stored CSV data |
| `/api-hashtags/` | GET | Extract unique hashtags from API data |
| `/csv-hashtags/` | GET | Extract unique hashtags from CSV data |
| `/api-hashtags/count/` | GET | Count occurrences of each hashtag (API data) |
| `/csv-hashtags/count/` | GET | Count occurrences of each hashtag (CSV data) |
| `/api-hashtags/sorted/` | GET | Hashtags from API data, ranked by frequency |
| `/csv-hashtags/sorted/` | GET | Hashtags from CSV data, ranked by frequency |
| `/csv-hashtags-likes/sorted/` | GET | Posts sorted by likes / retweets / replies |
| `/industry-analysis` | GET | Aggregate engagement by industry (Tourism, Sports, Tech, Fashion, Entertainment) |
| `/engagement-over-time/` | GET | Track engagement trends over time |
| `/report` | POST | Generate an automated data-profiling report (pandas-profiling) |
| `/check_data_quality` | POST | Run an automated data quality check on required fields |

Full interactive docs available at `/docs` once the server is running (Swagger UI).

---

## Repository Contents

| File | Description |
|---|---|
| `main.py` | FastAPI app entry point, router registration, server startup |
| `main_router.py` | Global API router definition |
| `router.py` | All social media API endpoints (fetch, save, query, analyze) |
| `helper.py` | Core logic — API fetching, CSV loading, hashtag extraction, data integration |
| `db_connection.py` | MongoDB (Motor async) connection setup |
| `date_time.py` | Timestamp helpers for record creation/updates |
| `responses.py` | Standardized API response formatting |
| `mock.py` | Sample/mock API response data used during development |
| `requirements.txt` | Python dependencies |
| `Hashtag_Virality_and_Engagement_Analysis_Report.pdf` | Full academic report |
| `Hashtag_Virality_and_engagement_ppt.pdf` | Summary slide deck |
| `Instructions_to_Set_Up_and_Run_the_Project.pdf` | Setup & run guide |

---

## Setup & Usage

```bash
# 1. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start MongoDB locally
mongod

# 4. Run the FastAPI server
uvicorn main:app --reload

# 5. Open the interactive API docs
# http://localhost:8000/docs
```

Load data into the pipeline:

```bash
curl -X POST http://localhost:8000/save-csv-data
curl -X POST http://localhost:8000/save-api-data
```

> **Note:** this repo excludes local config (API tokens, absolute file paths) — see the note below.

---

## Tech Stack

`Python` · `FastAPI` · `MongoDB` (`Motor` async driver) · `Pandas` · `NumPy` · `Regex` · `TF-IDF & Cosine Similarity` · `Matplotlib` / `Seaborn`

---

## Authors

**Any Das**, **Natnael Solomon Gebremichael**, **Tahira Rezaie**
CdLM Data Science, Università degli Studi di Milano-Bicocca
