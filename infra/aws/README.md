# AWS deploy-target reference

This directory is a documentation-grade Terraform stub for what an AWS
deployment of the recommendation quiz could look like. It is **not**
provisioned, validated against an AWS account, or part of CI. Treat it as a
diagram in HCL: it shows where the API, the database, and the static frontend
would land, and what knobs would matter.

## What's here

| File | Purpose |
|---|---|
| `main.tf` | Top-level composition: VPC, RDS, ECS, ALB, S3 + CloudFront |
| `variables.tf` | Inputs (region, environment, image tags, ...) |
| `outputs.tf` | Endpoint URLs for API, frontend, and DB |
| `versions.tf` | Provider version pinning |

## How it would work in practice

1. Build the API image (`apps/api/Dockerfile`) and push to ECR.
2. Build the web bundle (`apps/web` → `pnpm build`) and sync `dist/` to S3.
3. `terraform apply` creates the VPC, RDS Postgres, ECS Fargate task running
   the API behind an ALB, and a CloudFront distribution fronting the S3
   origin.
4. CloudFront's `/api/*` behavior would forward to the ALB; everything else
   serves from S3.

## Caveats

* No AWS account has been used to run `terraform plan` against these files.
  Variable defaults will need real subnet IDs, hosted zone names, and ACM
  certificate ARNs before they will plan cleanly.
* Secrets are referenced via SSM parameter ARNs but not populated.
* No autoscaling, WAF, observability (CloudWatch dashboards / alarms), or
  blue/green deployment is wired up. These would be the next layer.

## Why include it at all

To make the deploy story explicit: the project is hermetic and runnable
locally, but the seams for a real AWS deployment are documented and stubbed
in code rather than buried in a README paragraph.
