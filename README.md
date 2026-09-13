# Data Platform Engineering Lab

Production-style laboratory focused on modern data platform engineering, cloud-ready architecture, automation, observability, security, and CI/CD.

## Objectives

This repository is designed to demonstrate hands-on experience in:

- Data ingestion and integration
- Python-based data services
- Containerized workloads with Docker
- PostgreSQL and analytical data stores
- Data transformation workflows
- Pipeline orchestration
- Observability and monitoring
- Infrastructure as Code
- CI/CD with GitHub Actions
- Security and secrets management
- Cloud-ready architecture
- Microsoft Fabric integration
- Data governance and operational reliability

## Architecture

The platform will evolve incrementally from a local WSL2/Docker environment into a production-style, multi-service data platform.

```text
Sources
   |
   v
Ingestion Layer
   |
   v
Raw / Operational Storage
   |
   v
Transformation Layer
   |
   v
Curated Data
   |
   +--> APIs
   +--> Analytics
   +--> Microsoft Fabric
   +--> Monitoring



```

## Repository Structure

```text
src/
  ingestion/
  api/
  common/

pipelines/
transformations/

infrastructure/
  docker/
  terraform/

observability/
tests/
docs/
.github/workflows/
```

## Environment

Initial development environment:

- Windows 11
- WSL2
- Ubuntu 24.04 LTS
- Docker Engine
- Docker Compose
- Python 3.12
- Git / GitHub
- VS Code Remote WSL

## Status

Environment bootstrap in progress.
