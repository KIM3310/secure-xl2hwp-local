# secure-xl2hwp-local Terraform

Minimal Cloud Run deployment skeleton for `secure-xl2hwp-local`.

## Apply

```bash
terraform init
terraform apply \
  -var="project_id=your-project" \
  -var="image=asia-northeast3-docker.pkg.dev/your-project/apps/secure-xl2hwp-local:latest"
```

Use `env` to inject auth, signing, and directory-boundary configuration.
