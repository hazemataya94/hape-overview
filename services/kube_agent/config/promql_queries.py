POD_RESTART_RATE = 'sum(rate(kube_pod_container_status_restarts_total{namespace="{namespace}",pod="{pod}"}[5m]))'
NODE_CONDITIONS = 'kube_node_status_condition{node="{node}"}'
ALERT_STATUS = 'ALERTS{alertname="{alertname}"}'
COST_EXPORTER_UP = "hape_eks_deployment_cost_exporter_up"
COST_TOTAL_HOURLY = 'hape_eks_deployment_cost_total_usd{period="hourly"}'
COST_TOTAL_HOURLY_OFFSET = 'hape_eks_deployment_cost_total_usd{{period="hourly"}} offset {historical_offset}'
COST_WORKLOAD_HOURLY = 'hape_eks_deployment_cost_workload_max_hourly_usd{{namespace="{namespace}",name="{deployment}"}}'
COST_TOP_WORKLOADS_HOURLY = "topk({top_limit}, hape_eks_deployment_cost_workload_max_hourly_usd)"
COST_TOP_WORKLOADS_HOURLY_OFFSET = "topk({top_limit}, hape_eks_deployment_cost_workload_max_hourly_usd offset {historical_offset})"


if __name__ == "__main__":
    print(POD_RESTART_RATE)
