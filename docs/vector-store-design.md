# Vector Store Design

This document describes the S/4HANA-oriented vector store design used to support incident similarity search and historical learning for the PrismCorp Advisor Core system.

## Goals
- Persist incident metadata and embeddings for similarity-based retrieval.
- Support rapid query execution from the decision engine.
- Keep schema compatible with S/4HANA enterprise data.
- Enable auditability and explainability for recommendations.

## Recommended S/4HANA Schema

### Table: `ZPRISM_INCIDENTS`

| Column | Type | Description |
| --- | --- | --- |
| INCIDENT_ID | CHAR(32) | Primary key incident identifier |
| SHIPMENT_ID | CHAR(32) | Linked shipment or PO |
| PORT | CHAR(64) | Affected port or region |
| PRODUCT_ID | CHAR(64) | Product or part number |
| INCIDENT_TYPE | CHAR(32) | e.g. `delay`, `damage`, `quality` |
| SEVERITY | CHAR(16) | `low`, `medium`, `high`, `critical` |
| STATUS | CHAR(16) | `open`, `resolved`, `escalated` |
| CREATED_AT | TIMESTAMP | Incident creation time |
| RESOLVED_AT | TIMESTAMP | Resolution completion time |
| COST_IMPACT | DECIMAL(15,2) | Estimated cost or penalty exposure |
| CHOSEN_OPTION | CHAR(32) | Decision option selected |
| OUTCOME | CHAR(32) | `success`, `partial`, `failure` |
| RESOLUTION_HOURS | DECIMAL(8,2) | Time to resolution in hours |
| EMBEDDING | RAWSTRING | Serialized vector embedding for similarity |
| CONTEXT | STRING | Short incident summary |
| NOTES | STRING | Human-readable summary or rationale |

### Design notes
- `EMBEDDING` is stored as a serialized vector (e.g. JSON array, binary blob, or SAP HANA ARRAY type).
- `CONTEXT` supports semantic search metadata and helps explain retrieval matches.
- Keep frequent query columns indexed: `PORT`, `SEVERITY`, `STATUS`, `CREATED_AT`.

## Example S/4HANA Query Patterns

### 1. Retrieve recent incidents for a port
```sql
SELECT INCIDENT_ID,
       SHIPMENT_ID,
       PORT,
       SEVERITY,
       STATUS,
       CREATED_AT,
       COST_IMPACT,
       CHOSEN_OPTION,
       OUTCOME
FROM ZPRISM_INCIDENTS
WHERE PORT = 'Singapore'
  AND CREATED_AT >= ADD_DAYS( CURRENT_DATE, -30 )
ORDER BY CREATED_AT DESC;
```

### 2. Find unresolved high-severity incidents
```sql
SELECT INCIDENT_ID,
       SHIPMENT_ID,
       SEVERITY,
       STATUS,
       CREATED_AT,
       COST_IMPACT
FROM ZPRISM_INCIDENTS
WHERE SEVERITY IN ('high', 'critical')
  AND STATUS <> 'resolved'
ORDER BY CREATED_AT ASC;
```

### 3. Query by incident similarity (high-level pattern)
```sql
SELECT INCIDENT_ID,
       SHIPMENT_ID,
       PORT,
       SEVERITY,
       COST_IMPACT,
       EMBEDDING
FROM ZPRISM_INCIDENTS
WHERE PORT = :port
  AND STATUS = 'resolved'
ORDER BY /* similarity scoring over EMBEDDING */
LIMIT 10;
```
> Note: Actual similarity ranking may be executed in the application layer or via SAP HANA vector/ML extensions.

### 4. Aggregate KPIs for dashboard metrics
```sql
SELECT
  COUNT(*) AS total_incidents,
  SUM(CASE WHEN STATUS <> 'resolved' THEN 1 ELSE 0 END) AS open_incidents,
  SUM(CASE WHEN SEVERITY IN ('high','critical') THEN 1 ELSE 0 END) AS high_severity_incidents,
  AVG(RESOLUTION_HOURS) AS avg_resolution_hours,
  SUM(COST_IMPACT) AS total_cost_exposure
FROM ZPRISM_INCIDENTS
WHERE CREATED_AT >= ADD_DAYS( CURRENT_DATE, -30 );
```

## KPI Metrics Supported
- Total incidents in the last 30 minutes / 30 days
- Open incidents
- High-severity incidents
- Average resolution time
- Total cost exposure
- Recommendation outcome success rate

## Vector Store Usage
- The incident decision engine can call `query_vector_store(query)` to retrieve similar resolved incidents.
- Similar incident results are used to inform recommendation reasoning and confidence scoring.
- Store both metadata and embedding vectors for faster matching and auditability.

## Operational Considerations
- If S/4HANA supports native vector or ML functions, use those for similarity ranking.
- Otherwise, export embeddings to a lightweight vector engine and keep `ZPRISM_INCIDENTS` as the authoritative incident master.
- Maintain a regular cleanup policy for old incidents and archive resolved history after retention limits.
