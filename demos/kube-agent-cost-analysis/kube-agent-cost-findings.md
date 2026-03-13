# cost incident: payments/api

## Summary
No cost increases or threshold anomalies detected for cost 'api'.

## Likely Root Cause
unknown

## Evidence Summary
- prometheus.cost.exporter_up: exporter/eks-deployment-cost
- prometheus.cost.total_hourly_usd: namespace/payments
- prometheus.cost.total_hourly_usd.offset: namespace/payments
- prometheus.cost.workload_hourly_usd: deployment/payments/api
- prometheus.cost.top_workloads_hourly_usd: namespace/payments
- prometheus.cost.top_workloads_hourly_usd.offset: namespace/payments

## Debugging Steps
- cost-workload-hourly-threshold: Workload hourly metric is missing for deployment 'api'.
- cost-hourly-increase-ratio: Current or historical hourly cost metric is missing.
- cost-top-workloads-increase: Current or historical top workload metrics are missing.

## Suggested Fixes
- none

## Dashboard Links
- none

## AI Used
False

