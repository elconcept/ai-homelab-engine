# AI Homelab Engine — retired

This repository was retired on 2026-11-28. The homelab management centre is the private [elconcept/ai-homelab-vault](https://github.com/elconcept/ai-homelab-vault): configuration, secrets, task records and the central image workflow.

The deployment path is **GitHub source → GitHub Actions → Docker Hub → NAS Compose stacks**.

- Source checkouts belong in `/volume1/workspace`.
- Deployment Compose files, runtime configuration and service data belong in `/volume2/docker`.
- The NAS pulls images from Docker Hub.

The former GHCR build workflow, OpenTofu workflow and bootstrap IaC have been removed. This repository has no active Actions workflows. Its Git history remains available for reference.
