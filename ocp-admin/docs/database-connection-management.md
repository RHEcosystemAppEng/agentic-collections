---
title: Database Connection Management
category: operations
sources:
  - title: PostgreSQL pg_stat_activity view
    url: https://www.postgresql.org/docs/current/monitoring-stats.html#MONITORING-PG-STAT-ACTIVITY-VIEW
    date_accessed: 2026-05-05
  - title: Crunchy Data postgres_exporter
    url: https://github.com/CrunchyData/postgres_exporter
    date_accessed: 2026-05-05
  - title: Kubernaut Demo Scenarios - DB connection saturation golden transcript
    url: https://github.com/jordigilh/kubernaut-demo-scenarios/blob/feature/v1.4-new-scenarios/golden-transcripts/db-saturation-databaseconnectionpoolexhausted.json
    date_accessed: 2026-05-05
tags: [database, postgresql, connections, monitoring, performance, connection-pooling]
semantic_keywords: [database connections, connection pool, pg_stat_activity, max_connections, connection leak, connection saturation, pgbouncer, postgresql monitoring]
use_cases: [database-operations, performance-troubleshooting, capacity-planning]
related_docs: [day-2-operations.md, troubleshooting.md]
last_updated: 2026-05-05
---

# Database Connection Management

Monitoring, diagnosing, and resolving PostgreSQL connection saturation on OpenShift.

---

## Overview

PostgreSQL enforces a hard limit on concurrent connections (`max_connections`). When all slots are consumed, new clients receive `FATAL: remaining connection slots are reserved for non-replication superuser connections`. This affects all workloads sharing the database, not just the offending client. Early detection and connection pooling prevent outages.

---

## Key Metrics

### Connection Counts

Requires `postgres_exporter` (ServiceMonitor + Deployment or Sidecar):

```promql
# Active connections by database
pg_stat_activity_count{datname!=""}

# Total connections vs max
pg_stat_activity_count / pg_settings_setting{name="max_connections"}

# Connections by state (active, idle, idle in transaction)
pg_stat_activity_count{state="active"}
pg_stat_activity_count{state="idle"}
pg_stat_activity_count{state="idle in transaction"}
```

### Saturation Detection

**Connection usage above 80%**:
```promql
pg_stat_activity_count
  / on() pg_settings_setting{name="max_connections"} > 0.8
```

**Predict when connections will exhaust** (linear extrapolation):
```promql
predict_linear(pg_stat_activity_count[30m], 3600)
  > on() pg_settings_setting{name="max_connections"}
```

### Long-Running Queries

Queries holding connections for extended periods:
```promql
# Connections open for more than 5 minutes
pg_stat_activity_max_tx_duration{datname!=""} > 300
```

---

## Diagnosing Connection Saturation

### Step 1: Identify Current Connection Usage

```bash
# Connect to PostgreSQL pod
oc exec -n <namespace> deploy/postgresql -- \
  psql -U postgres -c "
    SELECT datname, state, count(*)
    FROM pg_stat_activity
    GROUP BY datname, state
    ORDER BY count(*) DESC;"
```

### Step 2: Find the Connection Leaker

```bash
# Show connections grouped by application/client
oc exec -n <namespace> deploy/postgresql -- \
  psql -U postgres -c "
    SELECT application_name, client_addr, state, count(*)
    FROM pg_stat_activity
    WHERE datname IS NOT NULL
    GROUP BY application_name, client_addr, state
    ORDER BY count(*) DESC;"
```

### Step 3: Identify Long-Held Connections

```bash
# Connections open for more than 5 minutes
oc exec -n <namespace> deploy/postgresql -- \
  psql -U postgres -c "
    SELECT pid, application_name, state, query,
           now() - state_change AS duration
    FROM pg_stat_activity
    WHERE state != 'idle'
      AND now() - state_change > interval '5 minutes'
    ORDER BY duration DESC
    LIMIT 10;"
```

### Step 4: Check max_connections and Reserved Slots

```bash
oc exec -n <namespace> deploy/postgresql -- \
  psql -U postgres -c "
    SHOW max_connections;
    SHOW superuser_reserved_connections;"
```

`superuser_reserved_connections` (default: 3) reserves slots for superuser access even when the pool is exhausted. This is critical for administrative recovery.

---

## Remediation

### Immediate: Terminate Leaking Connections

```bash
# Terminate idle connections from a specific application
oc exec -n <namespace> deploy/postgresql -- \
  psql -U postgres -c "
    SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE application_name = '<leaker>'
      AND state = 'idle';"
```

### Short-Term: Increase max_connections

```bash
# For OpenShift template-based PostgreSQL
oc set env deploy/postgresql \
  POSTGRESQL_MAX_CONNECTIONS=100 \
  -n <namespace>
```

Increasing `max_connections` is a stopgap. Each connection consumes ~5-10MB of shared memory. Values above 200 require careful memory planning.

### Long-Term: Deploy a Connection Pooler

PgBouncer multiplexes many client connections onto a smaller number of PostgreSQL connections:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pgbouncer
spec:
  replicas: 1
  template:
    spec:
      containers:
        - name: pgbouncer
          image: bitnami/pgbouncer:latest
          env:
            - name: POSTGRESQL_HOST
              value: postgresql.<namespace>.svc
            - name: POSTGRESQL_PORT
              value: "5432"
            - name: PGBOUNCER_POOL_MODE
              value: transaction
            - name: PGBOUNCER_DEFAULT_POOL_SIZE
              value: "20"
            - name: PGBOUNCER_MAX_CLIENT_CONN
              value: "200"
```

Pool modes:
- **session**: One server connection per client session (least efficient, most compatible)
- **transaction**: Server connection returned after each transaction (recommended for most workloads)
- **statement**: Server connection returned after each statement (most efficient, incompatible with multi-statement transactions)

---

## PrometheusRule Example

Alert when connection usage exceeds 80% for 5 minutes:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: database-connection-saturation
  namespace: <namespace>
spec:
  groups:
    - name: database-connections
      rules:
        - alert: DatabaseConnectionPoolExhausted
          expr: |
            pg_stat_activity_count > 0.8
              * on() pg_settings_setting{name="max_connections"}
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "PostgreSQL connection pool above 80% ({{ $value }} active)"
            description: >
              PostgreSQL in namespace {{ $labels.namespace }} has
              {{ $value }} active connections, exceeding 80% of
              max_connections. Investigate which workloads are consuming
              connections.
```

---

## postgres_exporter Setup

To expose PostgreSQL metrics to Prometheus:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres-exporter
spec:
  replicas: 1
  template:
    spec:
      containers:
        - name: exporter
          image: quay.io/prometheuscommunity/postgres-exporter:latest
          env:
            - name: DATA_SOURCE_NAME
              value: "postgresql://postgres:<password>@postgresql:5432/postgres?sslmode=disable"
          ports:
            - containerPort: 9187
              name: metrics
---
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: postgres-exporter
spec:
  selector:
    matchLabels:
      app: postgres-exporter
  endpoints:
    - port: metrics
      interval: 30s
```

Connect the exporter as a **superuser** to ensure it can query `pg_stat_activity` even when all regular connection slots are exhausted.

---

## Common Issues

### "FATAL: remaining connection slots are reserved"

All non-superuser slots are consumed. Superuser slots (`superuser_reserved_connections`) are reserved for recovery:

```bash
# Use superuser to investigate (these slots are reserved)
oc exec -n <namespace> deploy/postgresql -- \
  psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"
```

### Exporter Shows Stale Metrics During Saturation

If `postgres_exporter` connects as a regular user, it loses its connection during saturation and reports stale data. Always configure the exporter with superuser credentials.

### Connection Count Doesn't Match Application Expectations

Each pod may open multiple connections (one per thread/goroutine). Check:
```bash
# Connections per client IP
oc exec -n <namespace> deploy/postgresql -- \
  psql -U postgres -c "
    SELECT client_addr, count(*)
    FROM pg_stat_activity
    WHERE datname IS NOT NULL
    GROUP BY client_addr
    ORDER BY count(*) DESC;"
```

---

## Metric Discovery Protocol

When investigating database connections with Prometheus tools:

1. **Discover metrics**: Filter with `{__name__=~"pg_.*"}` to find all postgres_exporter metrics
2. **Check available databases**: `pg_stat_activity_count` has a `datname` label showing per-database counts
3. **Verify exporter health**: `pg_up` should be `1`; if `0`, the exporter lost its database connection
4. **Scope queries**: Add `{namespace="<target>"}` to target a specific PostgreSQL instance

---

## References

- [PostgreSQL pg_stat_activity](https://www.postgresql.org/docs/current/monitoring-stats.html#MONITORING-PG-STAT-ACTIVITY-VIEW)
- [PostgreSQL connection defaults](https://www.postgresql.org/docs/current/runtime-config-connection.html)
- [PgBouncer documentation](https://www.pgbouncer.org/config.html)
- [postgres_exporter](https://github.com/CrunchyData/postgres_exporter)
