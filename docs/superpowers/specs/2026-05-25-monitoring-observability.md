# Design Spec: Phase 6 - Monitoring and Observability

## Overview
Implement a comprehensive monitoring and observability stack for the Real-Time Product Recommendation System using Prometheus, Grafana, and FastAPI instrumentation.

## Components

### 1. FastAPI Instrumentation
- **Tool:** `prometheus-fastapi-instrumentator`
- **Goal:** Expose a `/metrics` endpoint and capture HTTP Golden Signals (Latency, Traffic, Errors).
- **Implementation:** 
    - Inject middleware into `src/dashboard/api.py`.
    - Update `requirements.api.txt`.

### 2. Infrastructure Monitoring
- **Tool:** `kube-prometheus-stack` (Helm Chart)
- **ServiceMonitor:** Automatically discover the FastAPI service in the `mlops` namespace.
- **Resource Tracking:** Monitor CPU/Memory for Airflow, Kafka, and Spark pods using existing exporters.

### 3. Automated Grafana Dashboard
- **Persistence:** ConfigMap with `grafana_dashboard: "1"` label.
- **Panels:**
    - HTTP Throughput (req/s)
    - P99 Latency
    - Error Rate (4xx/5xx)
    - Pod CPU/Memory Usage
    - Total Processed Recommendations (Business Metric)

## Security
- Metrics scraping is internal to the Kubernetes cluster network.
- No public exposure of the `/metrics` endpoint via Ingress.

## File Structure
- `monitoring/values-monitoring.yaml`
- `monitoring/servicemonitor.yaml`
- `monitoring/dashboard-recommender.json`
- `monitoring/grafana-dashboard.yaml`
