# The bootstrap stack deliberately creates no billable infrastructure.
# Successful tofu init+plan verifies the Cloudflare R2 backend credentials.
output "homelab_backend_smoke_test" {
  value = "r2-backend-initialized"
}
