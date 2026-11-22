# Example root backend. Pass S3-compatible R2 settings via tofu init -backend-config.
# Do not embed access keys in Terraform configuration.
terraform {
  backend "s3" {}
}
