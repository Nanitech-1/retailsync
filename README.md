# RetailSync: Multi-Source ETL Data Pipeline

![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)
![Database](https://img.shields.io/badge/database-PostgreSQL%2016%20%7C%20SQLite-blue.svg)
![CI/CD](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-green.svg)
![License](https://img.shields.io/badge/license-MIT-purple.svg)

**RetailSync** is an automated, production-grade data pipeline that integrates, standardizes, and models e-commerce retail data from three distinct sources into a clean PostgreSQL star-schema data warehouse.

---

## Architecture Overview

```mermaid
flowchart TD
    subgraph Sources ["1. Multi-Source Ingestion"]
        S1["Olist Brazilian E-commerce (CSVs)"]
        S2["DummyJSON Live REST API"]
        S3["Messy Supplier CSV (Synthetic ~2K rows)"]
    end

    subgraph Staging ["2. Staging Layer (stg_*)"]
        STG["Raw Staging Tables with _source & _ingested_at"]
    end

    subgraph Validation ["3. Validation & Quarantine"]
        VAL{"Validation Rules (Nulls, Types, Ranges, FKs)"}
        REJ[("rejected_records (Quarantined JSONB)")]
    end

    subgraph Enrichment ["4. LLM Standardization"]
        LLM["Gemini LLM Client + Cache (llm_cache)"]
    end

    subgraph Warehouse ["5. Star-Schema Data Warehouse"]
        DIM_C[("dim_customers")]
        DIM_P[("dim_products")]
        DIM_S[("dim_sellers")]
        DIM_D[("dim_date")]
        FACT[("fact_orders (Order Items Grain)")]
    end

    subgraph Analytics ["6. Business Analytics Views"]
        V1["v_revenue_by_category_monthly (LAG MoM)"]
        V2["v_top_products_by_category (DENSE_RANK)"]
        V3["v_repeat_customer_rate"]
        V4["v_delivery_delay_by_seller"]
        V5["v_supplier_vs_api_price_comparison"]
    end

    subgraph Audit ["7. Pipeline Audit & Monitoring"]
        MON[("pipeline_runs (Quality Score, Counts)")]
    end

    Sources --> STG
    STG --> VAL
    VAL -- "Failed Checks" --> REJ
    VAL -- "Valid Records" --> LLM
    LLM --> Warehouse
    Warehouse --> Analytics
    Warehouse --> MON
```

---

## Tech Stack
* **Language**: Python 3.11+
* **Database**: PostgreSQL 16 (production target via Docker Compose) & SQLite fallback for zero-dependency local runs
* **Libraries**: SQLAlchemy, pandas, psycopg2-binary, Pydantic, Tenacity, Requests, Pytest, Python-dotenv
* **LLM Engine**: Google Gemini API (`google-generativeai`) with caching and graceful fallbacks
* **CI/CD**: GitHub Actions

---

## Quickstart

### 1. Clone & Set Up Virtual Environment
```bash
git clone <repository_url>
cd retailsync
python -m venv .venv

# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1

# Install dependencies:
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
```
Edit `.env` with your database credentials or Gemini API key.

### 3. Initialize Database Schema
```bash
python -c "from src.load.db import init_schema; init_schema()"
```

### 4. Run Tests
```bash
pytest tests/
```

---

## Project Status

- [x] **Phase 1**: Repository scaffolding, Docker Compose, Star-Schema SQL, typed configuration, and structured logging.
- [ ] **Phase 2**: Multi-source ingestion (Olist, REST API, Supplier CSV generator).
- [ ] **Phase 3**: Validation engine and quarantined `rejected_records`.
- [ ] **Phase 4**: Idempotent warehouse loads and analytics views.
- [ ] **Phase 5**: LLM enrichment with caching and failure fallback.
- [ ] **Phase 6**: Pipeline monitoring, quality scoring, and alerting.
- [ ] **Phase 7**: End-to-end tests, documentation, and GitHub Actions CI/CD.
