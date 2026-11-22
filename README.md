# AI Homelab Engine

**Public compute & CI/CD execution engine for a private single-user AI homelab.**

This repository deliberately contains no plaintext service tokens, credentials, private documents or live Terraform state. Runtime authentication is through **GitHub Actions Secrets**. The private counterpart is `elconcept/ai-homelab-vault`.

## Why a public runner?

GitHub-hosted **standard** runners are free for public repositories. Use them for short-lived OpenTofu/Terraform, container builds and infrastructure experimentation. The free policy does not grant unlimited storage, unrestricted concurrency or free larger runners.

## Actions

| Workflow | Trigger | Functions |
| --- | --- | --- |
| `tofu-ops.yml` | Manual `workflow_dispatch` | `plan`, `apply`, `destroy` for a named stack directory |
| `docker-build-ghcr.yml` | Manual `workflow_dispatch` | Build a Docker image from a chosen source repository and push to GHCR |

There are no `pull_request_target` triggers. Jobs do not expose tokens in command output.

### OpenTofu layout

```text
iac/
  backend.tf                 # backend and configuration example
  providers.tf               # optional cloud provider requirements
  stacks/
    bootstrap/
      backend.tf             # remote R2 S3 state declaration
      main.tf                # no billable resources
.github/workflows/
  tofu-ops.yml
  docker-build-ghcr.yml
.env.example                 # variable names only, never values
```

`tofu-ops.yml` uses **Cloudflare R2** bucket `tfstate-homelab` as a remote S3-compatible state backend, with a different state key for each stack. Remote access requires `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, and `R2_DEFAULT_ENDPOINT` secrets (alternatively `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` where configured). The initial `bootstrap` stack provisions no real cloud services, allowing a safe remote-backend smoke test.

### Credentials and project selection

- Azure service principal variables: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_SUBSCRIPTION_ID`.
- Cloudflare: `CF_API_TOKEN` when required by a provider; an R2-only key may not grant Workers/DNS permissions.
- GitHub: prefer ephemeral `GITHUB_TOKEN` for GHCR; stored personal tokens only where strictly needed.
- GCP: local `gcloud-ws` and `gcloud-personal` profiles from Synology are **not** automatically available to ephemeral GitHub runners. Configure Workload Identity Federation or service-account credentials before running GCP IaC in Actions.

A local login does not substitute for cloud runner credentials.

## Operating principles

Keep all lifecycle actions enabled: `plan`, `apply`, `destroy`, `docker build`, `push`. No mandatory corporate gating or dev/prod separation. Use free tiers by default; check budget and remaining credits for temporary promotional accounts. Keep experiments distinct from the owner's legal workspace, NAS backups and unrelated personal data.

**Security boundary:** Only trusted maintainers should have write access to `main`. Workflows are manually dispatched, and third-party code built through the Docker workflow is not given infrastructure secrets. Never add a plaintext `.env` to this public repository.

**Cloud control plane:** `ai-admin-tools` at `ai.xlap.pl` aggregates Cloudflare, Portainer, Synology, Google Cloud, Azure and other MCP services; current availability is documented in the private vault.

## Verified execution

- 2026-11-22: [GHCR smoke workflow run #45041105017](https://github.com/elconcept/ai-homelab-engine/actions/runs/45041105017) completed successfully with the test `examples/hello/Dockerfile`.
- `tofu-ops.yml` is recognized and enabled by GitHub. Its remote R2 plan test remains pending until the repository's Actions Secrets have been populated.

## Cloudflare MCP registration

The manual workflow [`register-cloudflare-mcp.yml`](.github/workflows/register-cloudflare-mcp.yml) runs [`scripts/register_cloudflare_mcp.py`](scripts/register_cloudflare_mcp.py) and registers **nine** token-authenticated endpoints: Azure, GCP Workspace, GCP Personal, DS1821+ Desktop Commander, Hugging Face, GitHub, Render, Tavily and Resend. It preserves existing portal server entries and Code Mode.

All provider bearer tokens are already stored in GitHub Actions Secrets. The only missing credential is **`CF_API_TOKEN`**, a Cloudflare API token with the **MCP Portals Write** account permission, which is distinct from Cloudflare Access service-token credentials (`CF_CLIENT_*`). Add it to Actions Secrets before dispatching; no other secret values should be copied into workflow inputs.

Once present, run:

```bash
gh workflow run register-cloudflare-mcp.yml -R elconcept/ai-homelab-engine --ref main
```

The workflow must be followed by provider-level smoke tests. The script confirms registration and portal attachment but does not falsely assert working credentials or successful `tools/list` at each upstream.

Vercel and Supabase are intentionally **excluded** from this Bearer batch. Official Vercel MCP documents OAuth, not general acceptance of Vercel REST API tokens. Both previously failed OAuth registration through the Cloudflare API. Register them via Cloudflare GUI/OAuth, or test a separately supported method; do not create untested placeholder server records.

Upstash likewise requires additional account metadata (`UPSTASH_EMAIL`) for the local stdio server and is not yet included.
