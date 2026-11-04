# Telecom Network Activity Analytics Platform

A six-weekend data engineering portfolio project that will transform historical telecom activity into reliable analytics for Power BI and Tableau. The current implementation generates synthetic test batches and loads them into a local PostgreSQL raw layer. dbt models, orchestration, and dashboards are planned.

## Business questions

- How does internet, call, and SMS activity vary by time and geographic grid?
- Which grids have the greatest activity and which show unusual changes?
- How do weekday and weekend activity patterns differ?
- Are incoming batches complete and valid enough for reporting?

The planned public source is the [Telecom Italia Milan dataset](https://doi.org/10.7910/DVN/EGZHFV). Its records describe historical activity from 2013, aggregated over geographic grid squares and time intervals. The [dataset publication](https://www.nature.com/articles/sdata201555) describes activity values as proportional measures: do not label them as gigabytes, subscriber counts, physical cell KPIs, or current operational measurements.

**Data access:** The Dataverse entry lists custom terms. Review the dataset and grid-reference terms before downloading, redistributing, or publishing extracts. No public-source data is included in this repository. The synthetic fixtures below contain invented values and are not public-source observations.

## Planned architecture

```mermaid
flowchart LR
    A[Public activity files] --> C[Python ingestion]
    B[Synthetic replay fixtures] --> C
    C --> D[(PostgreSQL raw)]
    D --> E[dbt staging]
    E --> F[Dimensional warehouse]
    F --> G[Analytics marts]
    G --> H[Power BI]
    G --> I[Tableau]
    J[Airflow] -. orchestrates .-> C
    J -. orchestrates .-> E
    K[Tests and CI] -. validate .-> G
```

The synthetic replay fixtures will be used in isolated test runs, not blended into reports of public data. See [the six-weekend plan](docs/roadmap.md), [architecture decisions](docs/architecture.md), and [source contract](docs/data_contract.md).

## Run the synthetic fixture generator

Python 3.12 is available on the development machine. The generator uses only the Python standard library.

```powershell
cd telecom-network-activity-platform
python scripts/generate_fixture.py --output-dir data/generated/fixture
python -m unittest discover -s tests -p test_generate_fixture.py -v
```

The generator refuses to overwrite any existing fixture file. To generate another copy, choose a new output directory. Generated data is ignored by Git. It consists of a baseline batch, a late-arrival batch, a correction batch, and a manifest describing the deliberately injected errors.

## Run the raw ingestion layer locally

Prerequisites: Docker Desktop with Compose, Python 3.12, and port 5432 available on localhost. The first initialization creates a project-specific PostgreSQL volume; the SQL initialization scripts run only when that volume is first created.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
# Edit .env and replace POSTGRES_PASSWORD with a unique local development password.
docker compose up -d --wait
# Generate the fixture if you have not already done so.
if (-not (Test-Path 'data/generated/fixture/manifest.json')) { python scripts/generate_fixture.py --output-dir data/generated/fixture }

$env:PGHOST = '127.0.0.1'
$env:PGPORT = '5432'
$env:PGDATABASE = 'telecom_warehouse'
$env:PGUSER = 'telecom'
$env:PGPASSWORD = (Get-Content .env | Where-Object { $_ -like 'POSTGRES_PASSWORD=*' } | Select-Object -First 1).Substring('POSTGRES_PASSWORD='.Length)
.\.venv\Scripts\python.exe -m ingestion.load_activity data/generated/fixture/baseline.tsv --source-system synthetic
.\.venv\Scripts\python.exe -m ingestion.load_activity data/generated/fixture/late.tsv --source-system synthetic
.\.venv\Scripts\python.exe -m ingestion.load_activity data/generated/fixture/correction.tsv --source-system synthetic

# Opt in to integration tests against the project database.
$env:RUN_DB_TESTS = '1'
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

If you change the database name, user, or host port in `.env`, use matching `PGDATABASE`, `PGUSER`, and `PGPORT` values above. Do not commit `.env`. Use `docker compose stop` when finished; stopping preserves the database volume.

Ingestion hashes each file, logs batch counts, and stores accepted fields and rejects separately. Replaying the same bytes for the same source returns `already_loaded`. Accepted duplicates and corrections remain in raw data for the later dbt deduplication step. A malformed CSV stream rolls the batch back and records a failure when the database is available. Blank measures remain blank pending confirmation of the public-source semantics.

## Milestone status

| Stage | Status |
|---|---|
| 1. Scope, source design, and synthetic fixtures | Complete; public-source terms and file inspection pending |
| 2. Ingestion and PostgreSQL raw layer | Synthetic batch ingestion implemented; public source inspection pending |
| 3. dbt staging and dimensional models | Planned |
| 4. Incremental loading, marts, and Airflow | Planned |
| 5. Power BI and Tableau | Planned |
| 6. CI and portfolio documentation | Planned |

PostgreSQL is configured in Compose. Airflow has not yet been configured. See the roadmap for acceptance criteria.

