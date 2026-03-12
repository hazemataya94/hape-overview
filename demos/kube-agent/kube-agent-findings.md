# pod incident: kube-agent-test/kube-agent-api-78d57f77dc-f4h9r

## Summary
Detected 3 likely cause(s) for pod 'kube-agent-api-78d57f77dc-f4h9r': oom-kill, probe-failure, deployment-revision-change.

## Likely Root Cause
oom-kill

## Evidence Summary
- kubernetes.pod.status: pod/kube-agent-test/kube-agent-api-78d57f77dc-f4h9r
- kubernetes.pod.events: pod/kube-agent-test/kube-agent-api-78d57f77dc-f4h9r
- kubernetes.pod.logs: pod/kube-agent-test/kube-agent-api-78d57f77dc-f4h9r
- kubernetes.pod.owner: pod/kube-agent-test/kube-agent-api-78d57f77dc-f4h9r

## Debugging Steps
- oom-kill: Pod restart appears linked to OOMKilled events.
- probe-failure: Probe failure pattern found in pod events.
- deployment-revision-change: Recent deployment revision change detected.

## Suggested Fixes
- Increase memory request/limit or reduce memory pressure in workload.

## Dashboard Links
- [Kubernetes Namespace Pods](http://localhost:3000/d/k8s-namespace-pods?var-namespace=kube-agent-test)
- [Kubernetes Pod Resources](http://localhost:3000/d/k8s-pod?var-namespace=kube-agent-test&var-pod=kube-agent-api-78d57f77dc-f4h9r)
- [Kubernetes Pods Overview](http://localhost:3000/d/k8s-views-pods?var-namespace=kube-agent-test&var-pod=kube-agent-api-78d57f77dc-f4h9r)

## AI Used
False
