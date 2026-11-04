# Architecture decisions

## Project scope

Analyze historical telecommunications activity by geographic grid and 10-minute interval. Source values are anonymized activity measures, not network availability, throughput, subscriber counts, or data volume in GB. A geographic grid square is not a physical network cell.

## Planned flow

1. Python reads daily public files in chunks and logs file name, checksum, batch ID, ingestion time, accepted rows, and rejects.
2. Raw PostgreSQL tables retain source values and ingestion metadata. Original input files remain separately accessible and are excluded from Git.
3. dbt staging casts and standardizes fields; intermediate models prepare reusable transformations.
4. A dimensional fact and dimensions support daily and geographic analytics marts.
5. Tests and reconciliation checks decide whether data is ready for Power BI and Tableau.
6. Airflow orchestrates the jobs and reports failures. GitHub Actions checks changes against small synthetic fixtures.

## Model design

The fact grain is one row per source system, grid square, 10-minute interval, and country code. The first 50,000 public-data rows have no duplicate key at that grain; this does not prove uniqueness for the complete dataset. Dimensions are date, grid, and country code. The country code denotes the telecommunications context described by the source; it is not the physical location of the grid.

Measures retain their source meaning and provenance. Synthetic and public records coexist in the local test warehouse and are identified by `source_system`; public-data queries must explicitly filter to `telecom_italia_milan`. The grid geometry reference will only be included once its access terms and join keys have been checked.

## Local constraints

Use PostgreSQL on host port 5432 and Airflow on 8080 if still free at deployment time. Bind local development interfaces to localhost. Process large source files in chunks and keep the Airflow configuration modest for a 16 GB Windows machine. No cloud infrastructure is required.

## Incremental design to validate in implementation

The public files are historical; any daily loads are a replay, not a live feed. Keep a batch-level ingestion timestamp and a deterministic source key. Later synthetic batches simulate late arrivals and corrections. Reprocess affected keys and their affected aggregate periods, then test that repeated loads are idempotent. Define a documented backfill procedure for changes outside the replay window.

