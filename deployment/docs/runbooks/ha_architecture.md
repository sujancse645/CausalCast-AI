# High Availability (HA) Guide
- Backend is scaled to multiple replicas using HPA.
- PostgreSQL should be deployed using Patroni for HA.
- Redis should be deployed in Sentinel or Cluster mode.
- Nginx Ingress handles load balancing.
