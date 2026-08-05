# Kubernetes Security Advanced

## ClusterRole (cluster-wide)

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: secret-reader
rules:
- apiGroups: [""]
  resources: ["secrets"]
  verbs: ["get"]
  resourceNames: ["app-credentials"]  # Restrict to specific

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: admin-binding
subjects:
- kind: User
  name: admin@example.com
  apiGroup: rbac.authorization.k8s.io
roleRef:
  kind: ClusterRole
  name: cluster-admin
  apiGroup: rbac.authorization.k8s.io
```

## Secrets Management

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque
stringData:
  username: admin
  password: secretpassword
```

### Mount as env
```yaml
env:
- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: db-credentials
      key: password
```

### Mount as volume
```yaml
volumeMounts:
- name: secret-volume
  mountPath: /etc/secrets
  readOnly: true
volumes:
- name: secret-volume
  secret:
    secretName: db-credentials
```

## Allow DNS (most apps need this)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
spec:
  podSelector: {}
  policyTypes: [Egress]
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - { protocol: UDP, port: 53 }
```

## Security Checklist

- [ ] RBAC scoped to least privilege
- [ ] Pod Security Standards set to restricted
- [ ] Network policies: deny by default, allow explicitly
- [ ] Containers run as non-root
- [ ] Root filesystem mounted read-only
- [ ] All capabilities dropped
- [ ] Sensitive data kept in Secrets
- [ ] Image scanning turned on
- [ ] Pull from a private registry
- [ ] Resource quotas and limits in place
- [ ] Audit logging switched on
- [ ] Credentials rotated on a schedule
