# Provider catalog for optional cloud stacks. Individual stacks can use a subset.
terraform {
  required_version = ">= 1.9.0"
  required_providers {
    cloudflare = { source = "cloudflare/cloudflare", version = ">= 5.0.0" }
    google     = { source = "hashicorp/google", version = ">= 6.0.0" }
    azurerm    = { source = "hashicorp/azurerm", version = ">= 4.0.0" }
    github     = { source = "integrations/github", version = ">= 6.0.0" }
  }
}
# Configure provider credentials through GitHub Actions secrets / environment.
# GitHub runners do NOT inherit the gcloud profiles stored on Synology.
