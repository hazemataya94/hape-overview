POD_RESTART_RATE = 'sum(rate(kube_pod_container_status_restarts_total{namespace="{namespace}",pod="{pod}"}[5m]))'
NODE_CONDITIONS = 'kube_node_status_condition{node="{node}"}'
ALERT_STATUS = 'ALERTS{alertname="{alertname}"}'


if __name__ == "__main__":
    print(POD_RESTART_RATE)
