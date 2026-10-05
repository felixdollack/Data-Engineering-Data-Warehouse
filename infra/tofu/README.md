# Sparkify AWS infrastructure

This OpenTofu configuration creates a classic, single-node Redshift cluster and its supporting resources from scratch:

- A dedicated VPC, two public subnets in separate availability zones, an internet gateway, and routes.
- A Redshift security group that admits TCP 5439 only from the required `allowed_ingress_cidr`.
- A Redshift subnet group and one `dc2.large` cluster in `us-east-1` by default.
- A Redshift service role with read/list access limited to the Udacity song and log dataset paths.
- Redshift-managed admin credentials stored in AWS Secrets Manager.

The cluster is publicly reachable only from the client CIDR you provide. This is intended for the Sparkify course project and short-lived analysis, not production workloads. Redshift is billed while running, and Secrets Manager also has a small ongoing charge. The cluster configuration disables automated snapshots and skips the final snapshot on destroy, so destroying the stack permanently deletes the warehouse data.

## Prerequisites

- OpenTofu or Terraform and AWS CLI installed.
- A separate AWS CLI profile named `sparkify` with permissions to create/delete Redshift, VPC, EC2 security/networking, IAM roles and policies, pass the Redshift role to the service, and manage the generated Secrets Manager credentials. SSO profiles work too.
- A trusted public IPv4 CIDR for your client, usually your current public IP with `/32`.

Configure and verify the profile without changing the work `default` profile:

```bash
aws configure sso --profile sparkify
aws sso login --profile sparkify
aws sts get-caller-identity --profile sparkify
```

For access-key credentials, use `aws configure --profile sparkify` instead. Never put AWS keys or database passwords in this directory.

## Plan and create

From the project root, set the allowed client CIDR and initialize OpenTofu:

```bash
export TF_VAR_allowed_ingress_cidr="YOUR_PUBLIC_IP/32"
tofu -chdir=infra/tofu init
tofu -chdir=infra/tofu fmt -check
tofu -chdir=infra/tofu validate
tofu -chdir=infra/tofu plan -out=sparkify.tfplan
```

Review the plan, especially the AWS account, region, public endpoint, and resources that will incur charges. Then create the stack only when ready:

```bash
tofu -chdir=infra/tofu apply sparkify.tfplan
```

The plan command does not create AWS resources. This HCL uses the standard AWS provider and can also be used with Terraform; run `terraform init` and its corresponding commands if you choose Terraform instead.

## Configure the ETL

After apply completes, copy the `redshift_host`, `redshift_port`, `redshift_database`, `redshift_username`, and `redshift_iam_role_arn` outputs into the matching fields in `dwh.cfg`. Get the admin password from the AWS Secrets Manager secret identified by `redshift_password_secret_arn`, and enter it in the local `dwh.cfg`. Keep that file private and out of version control. AWS rotates the managed password periodically, so refresh the local config if the database login stops working.

Then run `python create_tables.py` and `python etl.py` from the project root. The COPY commands read the public course data in `us-west-2` using the attached IAM role.

## Remove resources

When finished, remove the cluster and networking resources to stop Redshift compute charges:

```bash
tofu -chdir=infra/tofu destroy
```

This stack has no final snapshot configured. Destroy permanently removes the Redshift data and deletes its managed credentials secret. Review the destroy plan before confirming.
