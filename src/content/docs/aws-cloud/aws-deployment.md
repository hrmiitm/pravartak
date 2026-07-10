---
title: Deploying on AWS
description: A beginner-friendly guide to S3, Bedrock, EC2, and Lambda, with a secure deployment path and cleanup checklist.
sidebar:
  order: 1
---

By the end of this lesson, you will be able to choose the right AWS service for a workload, deploy static files, call a foundation model without managing model servers, distinguish a virtual machine from a serverless function, and sketch a secure AI web application.

<div class="slide-cta">
  <p><strong>Review with slides</strong><br/><small>12 slides · notes · drawing tools · PDF</small></p>
  <a href="../../slides/aws-deployment/">Open slide deck →</a>
</div>

:::caution[Before you create resources]
AWS resources may incur charges. Choose one region, create a budget alert, tag every resource, and complete the cleanup section. Never paste access keys into code or commit them to Git.
:::

## The four services in one picture

| Service | Mental model | Best fit | You manage |
|---|---|---|---|
| **Amazon S3** | A durable object store | Static assets, datasets, backups | Objects, access, lifecycle |
| **Amazon Bedrock** | Managed access to foundation models | Text/image generation, embeddings, agents | Model choice, prompts, safety, evaluation |
| **Amazon EC2** | A rented virtual machine | Long-running or highly customized servers | OS, patches, process, scaling |
| **AWS Lambda** | A function run on demand | Events, small APIs, bursty jobs | Function code, configuration, dependencies |

They often work together:

```text
Browser → CloudFront → private S3 bucket
       → API Gateway → Lambda → Amazon Bedrock
                              ↘ logs in CloudWatch
```

An EC2 service can replace Lambda when you need a continuously running process, custom operating-system packages, long requests, or predictable sustained compute.

## AWS foundations you need first

### Region

A **Region** is a geographic area containing multiple isolated Availability Zones. Most resources belong to one Region. Keep related resources together while learning: it reduces latency, confusion, and cross-Region transfer.

Not every Bedrock model is offered in every Region. Select the Region first, then choose an available model and keep that model ID in configuration rather than source code.

### IAM: authentication and authorization

AWS Identity and Access Management (IAM) answers two questions:

1. **Who is making this request?** A human identity, role, or AWS service.
2. **What may it do?** Policies allow particular actions on particular resources.

Use IAM Identity Center or another temporary-credential flow for people. Give workloads **roles**: an EC2 instance profile for EC2 and an execution role for Lambda. A role supplies temporary credentials automatically, so the application does not need stored access keys.

Apply least privilege. Start from the actions the application actually calls, test, and narrow the resource scope where the service supports it.

### Tags and budgets

Use tags such as `Project=pravartak`, `Environment=learning`, and `Owner=<your-name>`. Tags make cost review and cleanup much easier. A budget is an alert, not a hard spending cap, so still delete unused resources.

## Amazon S3: deploy static files

S3 stores **objects** inside **buckets**. An object has a key (similar to a path), content, metadata, and permissions. S3 is not a general-purpose server: it does not run Python, Node.js, or a database.

### Fast learning path: the S3 website endpoint

For a disposable public demo:

1. Build your site so the output is in `dist/`.
2. Create a globally unique bucket in your chosen Region.
3. In **Properties**, enable **Static website hosting** and set `index.html` as the index document.
4. For this public demo only, change Block Public Access and add a read-only bucket policy for `s3:GetObject`.
5. Upload the build:

```bash
aws s3 sync dist/ s3://YOUR_UNIQUE_BUCKET --delete
```

6. Open the website endpoint shown in the bucket properties.

The direct S3 website endpoint supports HTTP, not HTTPS. AWS recommends keeping Block Public Access enabled and using CloudFront with origin access control (OAC) for a secure site. See the [official S3 website tutorial](https://docs.aws.amazon.com/AmazonS3/latest/userguide/HostingWebsiteOnS3Setup.html).

### Production pattern: private S3 + CloudFront

Use this pattern for a real site:

- Keep the bucket private and leave Block Public Access enabled.
- Create a CloudFront distribution with the bucket as its origin.
- Use **origin access control** so only CloudFront reads the objects.
- Redirect viewers to HTTPS.
- Add a custom domain and an ACM certificate when needed.
- Invalidate changed HTML after a release; use hashed filenames and long cache lifetimes for CSS/JS assets.

This gives HTTPS, caching near users, and a smaller public attack surface. AWS provides a [secure static website walkthrough](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/getting-started-secure-static-website-cloudformation-template.html).

### Common S3 mistakes

- Uploading source files instead of the generated `dist/` directory.
- Making an entire bucket public when CloudFront OAC can keep it private.
- Using aggressive caching for `index.html`, then wondering why releases look stale.
- Forgetting `--delete`, leaving removed pages available.
- Putting API secrets in frontend JavaScript. Everything shipped to a browser is public.

## Amazon Bedrock: use foundation models

Bedrock provides managed access to foundation models. You send an inference request and receive a result; you do not patch or operate the underlying model server.

### A reliable first request

1. Open the Bedrock console in your chosen Region.
2. Choose a model from the model catalog and confirm its access requirements. Some third-party models require marketplace permissions or first-use information. The [current model-access guide](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html) is the source of truth.
3. Test the model in a playground.
4. Give your local identity or workload role permission to invoke only the models it needs.
5. Put the selected model ID in `BEDROCK_MODEL_ID`.

```python
import os
import boto3

client = boto3.client("bedrock-runtime", region_name="us-east-1")

response = client.converse(
    modelId=os.environ["BEDROCK_MODEL_ID"],
    messages=[
        {
            "role": "user",
            "content": [{"text": "Explain object storage in three sentences."}],
        }
    ],
    inferenceConfig={"maxTokens": 250, "temperature": 0.2},
)

print(response["output"]["message"]["content"][0]["text"])
```

The Converse API gives a common message shape across supported conversational models. The lower-level Invoke APIs use model-specific bodies and are useful when you need features not exposed by Converse. Review the [Bedrock inference API guide](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-api.html).

### Production concerns

- **Quality:** keep a small evaluation set; model output is probabilistic.
- **Cost:** cap output tokens, choose the smallest model that meets the target, and monitor usage.
- **Latency:** stream where supported and make timeouts explicit.
- **Privacy:** classify data before sending it and avoid logging sensitive prompts.
- **Safety:** validate inputs and outputs; add guardrails where appropriate, but do not treat a guardrail as the only control.
- **Resilience:** retry only transient errors with exponential backoff and jitter. Never retry every failure forever.

## Amazon EC2: run a server you control

An EC2 instance is a virtual machine. You choose an image, instance type, network, storage, and access method. EC2 is flexible because the operating system is yours; that flexibility also creates operational work.

### Beginner deployment sequence

1. Choose a current Linux AMI and a small instance type suitable for the lab.
2. Place it in a VPC subnet. Assign a public address only if the design requires direct internet access.
3. Attach an IAM role for AWS API calls. Do not copy credentials onto the machine.
4. Create a security group:
   - Prefer Systems Manager Session Manager for administration.
   - If SSH is necessary, allow port 22 only from your current IP, never `0.0.0.0/0`.
   - Allow application traffic only on required ports, normally 80 and 443 through a load balancer or reverse proxy.
5. Install the runtime, deploy the application, and run it under a process manager such as `systemd`.
6. Send logs and metrics to CloudWatch, patch the OS, and define backup/replacement procedures.

Security groups are stateful virtual firewalls applied to network interfaces. AWS documents the rule model in [EC2 security groups](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html).

### When EC2 is the better choice

Choose EC2 when you need a long-running worker, custom system packages, a local model needing a GPU, a persistent network connection, or steady compute where instance pricing is predictable. Prefer an immutable deployment: build an image or repeatable bootstrap, replace unhealthy instances, and avoid hand-edited “pet” servers.

### EC2 operational checklist

- Patch the OS and application dependencies.
- Restrict inbound traffic; do not expose database or model ports publicly.
- Use an IAM role and Secrets Manager or Parameter Store for secrets.
- Encrypt storage, capture logs, and create alarms.
- Put production instances behind a load balancer and an Auto Scaling group.
- Stop or terminate lab instances when finished. Stopped instances can still leave billable storage or addresses.

## AWS Lambda: run code on demand

Lambda runs a handler when an event arrives. AWS provisions the runtime and scales concurrent executions. You pay for requests and execution rather than keeping a VM running continuously.

Lambda works well for small APIs, queue consumers, file-processing events, schedules, and glue code. A single invocation can run for at most 900 seconds (15 minutes), so it is not a fit for an indefinitely running service; see the [current Lambda quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html).

### A Bedrock-backed Lambda handler

```python
import json
import os
import boto3

bedrock = boto3.client("bedrock-runtime")

def lambda_handler(event, context):
    body = json.loads(event.get("body") or "{}")
    prompt = str(body.get("prompt", "")).strip()
    if not prompt or len(prompt) > 4_000:
        return response(400, {"error": "prompt must contain 1–4000 characters"})

    result = bedrock.converse(
        modelId=os.environ["BEDROCK_MODEL_ID"],
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": 400, "temperature": 0.2},
    )
    answer = result["output"]["message"]["content"][0]["text"]
    return response(200, {"answer": answer})

def response(status, body):
    return {
        "statusCode": status,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body),
    }
```

Configure it with:

- A supported Python runtime and an explicit timeout (for example, 30 seconds).
- `BEDROCK_MODEL_ID` as an environment variable.
- An execution role that can write logs and invoke the selected model.
- Reserved concurrency or upstream throttling to limit unexpected load and spend.
- API Gateway for a public HTTP API, including authentication, validation, CORS, and rate limits.

Initialize SDK clients outside the handler so warm invocations can reuse them. Package and pin the SDK in production if you rely on a particular version. Do not return raw exceptions to callers; log a correlation ID and return a safe error.

### Lambda or EC2?

| Question | Prefer Lambda | Prefer EC2 |
|---|---|---|
| Traffic shape | Bursty or event-driven | Continuous and predictable |
| Execution | Short, stateless work | Long-running process |
| Environment | Supported runtime is enough | OS-level control required |
| Scaling | Automatic per invocation | You control instances/scaling group |
| Operations | Minimal server management | Full control and responsibility |

## Capstone: a secure AI learning app

Build the system in layers so each layer can be verified:

1. **Frontend:** build static HTML/CSS/JS and place it in a private S3 bucket.
2. **Delivery:** serve the bucket through CloudFront with OAC and HTTPS.
3. **API:** create an API Gateway HTTP route that invokes Lambda.
4. **Inference:** let the Lambda role call one Bedrock model.
5. **Controls:** validate prompt length, require authentication, rate-limit requests, cap model output, and record latency/error metrics.
6. **Observability:** use structured logs without storing sensitive prompt bodies.

The browser must never receive AWS credentials. It calls your authenticated API; the Lambda execution role receives temporary credentials inside AWS.

### Verification checklist

- [ ] Static pages load through HTTPS and the S3 bucket is not public.
- [ ] Refreshing a nested route behaves as expected.
- [ ] An empty or oversized prompt receives a `400` response.
- [ ] The API rejects unauthenticated requests if authentication is required.
- [ ] Lambda can invoke only the intended model and write logs.
- [ ] Bedrock timeouts and throttling return a controlled error.
- [ ] Logs contain request IDs and timings, not secrets.
- [ ] A budget and service alarms are active.

## Knowledge check

1. Why should a production S3 website normally use CloudFront and OAC?
2. Why is an IAM role safer than an access key stored on an EC2 instance?
3. What workload characteristic would make EC2 a better fit than Lambda?
4. Where should the Bedrock model ID live, and why?
5. What prevents a public AI endpoint from creating unlimited model spend?

<details>
<summary>Suggested answers</summary>

1. It keeps the bucket private while adding HTTPS and edge caching.
2. A role supplies short-lived credentials automatically and avoids a long-lived secret on disk.
3. Examples include a long-running process, custom OS/GPU requirements, or sustained compute.
4. In deploy-time configuration such as an environment variable, because availability and choices vary by Region and can change.
5. Authentication, validation, rate limiting, concurrency limits, token limits, monitoring, and budgets work together.

</details>

## Assignment

Design the capstone architecture for a small class of 50 learners. Submit:

1. A diagram showing CloudFront, S3, API Gateway, Lambda, Bedrock, IAM, and CloudWatch.
2. A five-sentence explanation of why you chose Lambda or EC2 for the API.
3. A least-privilege permission list for each workload role.
4. Three failure cases and the user-visible behavior for each.
5. A cost-control and cleanup checklist.

## Cleanup

When the lab is over:

1. Disable/delete the API route and Lambda function.
2. Terminate EC2 lab instances and remove unneeded volumes, snapshots, load balancers, and allocated addresses.
3. Disable and delete the CloudFront distribution if it was only for the lab.
4. Empty and delete S3 lab buckets.
5. Remove lab IAM roles and policies after confirming nothing uses them.
6. Review the Billing console by service and Region; a deleted application can leave supporting resources behind.

You now have the central AWS deployment decision: **S3 stores static assets, Bedrock provides model inference, Lambda runs short event-driven code, and EC2 runs servers you control.**
