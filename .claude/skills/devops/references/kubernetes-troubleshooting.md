# Kubernetes Troubleshooting

## Debugging Workflow

```bash
# 1. Overview
kubectl get pods -o wide
kubectl get events -n <namespace> --sort-by='.lastTimestamp'

# 2. Details
kubectl describe pod <pod-name>

# 3. Logs
kubectl logs <pod-name>
kubectl logs <pod-name> --previous  # Crashed instance
kubectl logs <pod-name> -c <container>
```

## Common Pod States

| State | Cause | Solution |
|-------|-------|----------|
| Pending | Nothing free to schedule on | Look at node capacity |
| ContainerCreating | Still pulling the image | Confirm the image URI |
| CrashLoopBackOff | Container keeps dying | Read logs, review health checks |
| ImagePullBackOff | Pull never succeeded | Check registry credentials |
| OOMKilled (137) | Hit the memory ceiling | Raise the memory limit |

## Service & Network

```bash
kubectl exec -it <pod-name> -- nslookup kubernetes.default
kubectl exec -it <pod-name> -- curl http://myservice:8080
kubectl get endpoints <service-name>
kubectl port-forward service/myservice 8080:8080
kubectl get networkpolicies -A
```

## Quick Fixes

| Problem | Command |
|---------|---------|
| Pod won't terminate | `kubectl delete pod <name> --grace-period=0 --force` |
| CPU spiking | `kubectl top pods -A --sort-by=cpu` |
| Memory spiking | `kubectl top pods -A --sort-by=memory` |
| Force a restart | `kubectl rollout restart deployment/<name>` |
| Undo a rollout | `kubectl rollout undo deployment/<name>` |

For node issues, HPA, and anti-patterns, see `kubernetes-troubleshooting-advanced.md`.
