# cost incident: payments/__all__

## Summary
Cost analysis findings: Total hourly cost 40.00 USD is above threshold 20.00 USD. Hourly cost increase ratio is 4.00 and is above threshold 1.50. Detected increased workload costs in the last window: payments/api (+3.00 USD/h), payments/worker (+1.00 USD/h).

## Likely Root Cause
cost-total-hourly-threshold

## Evidence Summary
- prometheus.cost.exporter_up: exporter/eks-deployment-cost
- prometheus.cost.total_hourly_usd: namespace/payments
- prometheus.cost.total_hourly_usd.offset: namespace/payments
- prometheus.cost.workload_hourly_usd: namespace/payments
- prometheus.cost.top_workloads_hourly_usd: namespace/payments
- prometheus.cost.top_workloads_hourly_usd.offset: namespace/payments

## Debugging Steps
- cost-total-hourly-threshold: Total hourly cost 40.00 USD is above threshold 20.00 USD.
- cost-hourly-increase-ratio: Hourly cost increase ratio is 4.00 and is above threshold 1.50.
- cost-top-workloads-increase: Detected increased workload costs in the last window: payments/api (+3.00 USD/h), payments/worker (+1.00 USD/h).

## Suggested Fixes
- Review namespace-wide resource requests and right-size high-request workloads.
- Review recent deployment/config changes and compare request growth against baseline.
- Review workloads with increased hourly cost and compare resource requests and replicas against one-hour baseline.

## Dashboard Links
- [Pod dashboard](http://localhost:3000/d/pod)

## AI Used
False
