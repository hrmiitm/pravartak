---
marp: true
title: AWS Deployment Essentials
description: S3, Bedrock, EC2, and Lambda for beginners
theme: default
size: 16:9
paginate: true
---

<!-- _class: lead -->
<!-- _paginate: false -->

# AWS Deployment Essentials

S3 · Bedrock · EC2 · Lambda  
Four services. One deployable system.

<!-- notes
Start with the outcome: understand what each service owns and when to choose it. Recall which service names already feel familiar.
-->

---

## The mental models

| Service | Think of it as | Best for |
|---|---|---|
| **S3** | Object store | Files and static sites |
| **Bedrock** | Model API | Managed AI inference |
| **EC2** | Virtual machine | Long-running servers |
| **Lambda** | On-demand function | Events and small APIs |

<!-- notes
These are deliberately simplified mental models. They are accurate enough to make the first architecture decision before adding detail.
-->

---

## Start with identity, not code

1. Choose one **Region**
2. Give people temporary access
3. Give workloads **IAM roles**
4. Grant only required actions
5. Add project tags and a budget

> Never place an AWS access key in source code.

<!-- notes
Authentication identifies the caller and authorization decides what it may do. Roles remove the need to store long-lived keys on EC2 or Lambda.
-->

---

## S3 stores the frontend

```bash
npm run build
aws s3 sync dist/ s3://YOUR_BUCKET --delete
```

- Upload the **generated** site, not its source
- `index.html` changes often
- Hashed CSS/JS can be cached for a long time
- Frontend code can never contain secrets

<!-- notes
The --delete flag makes the bucket match the build output, but it also deserves care: always confirm the bucket name. Notice the different cache needs of HTML and hashed assets.
-->

---

## Production static hosting

**Viewer** → HTTPS → **CloudFront** → OAC → **Private S3**

- Keep Block Public Access enabled
- Let only CloudFront read objects
- Add HTTPS, caching, and a custom domain
- Invalidate changed HTML after release

<!-- notes
The direct S3 website endpoint is useful for a disposable lesson, but it is HTTP-only and public. Private S3 plus CloudFront is the production pattern.
-->

---

## Bedrock provides model inference

```python
result = bedrock.converse(
    modelId=os.environ["BEDROCK_MODEL_ID"],
    messages=[{
        "role": "user",
        "content": [{"text": prompt}],
    }],
)
```

You manage prompts, evaluation, safety, latency, and cost — not the model server.

<!-- notes
Model availability varies by Region, so configuration is better than hardcoding. Some models have first-use requirements. Demonstrate in the playground before writing code.
-->

---

## EC2 gives you a whole server

Choose EC2 for:

- Long-running processes
- Custom OS packages or GPUs
- Persistent connections
- Predictable, sustained compute

You own patching, networking, processes, scaling, logs, and recovery.

<!-- notes
Flexibility is not free: it moves responsibility to the team. A process working in an SSH session is not a deployment; it needs a service manager and restart policy.
-->

---

## Lock down the EC2 network

- Prefer Session Manager for administration
- If SSH is required: port 22 from **your IP only**
- Expose only required application ports
- Never expose databases or model servers publicly
- Attach a role; do not copy credentials onto disk

<!-- notes
Security groups are stateful virtual firewalls. Consider why 0.0.0.0/0 on SSH is dangerous, and why an application role should have fewer permissions than an administrator.
-->

---

## Lambda runs on demand

**Event arrives** → runtime starts/reuses → handler runs → response

Good fits:

- Small HTTP APIs
- Queue and file events
- Scheduled jobs
- Bursty, stateless work

One invocation is time-limited; it is not an always-on server.

<!-- notes
Lambda can scale quickly, so cost controls and downstream quotas matter. Its maximum invocation duration is 15 minutes, but learners should design much shorter API timeouts.
-->

---

## Lambda or EC2?

| Ask | Lambda | EC2 |
|---|---|---|
| Traffic | Bursty | Continuous |
| Work | Short, stateless | Long-running |
| Control | Runtime-level | OS-level |
| Scaling | Per invocation | Instances |
| Operations | Lower | Higher |

<!-- notes
There is no universally best service. Work backwards from execution duration, environment needs, traffic shape, team operations, and cost.
-->

---

## Capstone architecture

```text
Browser → CloudFront → private S3
       → API Gateway → Lambda → Bedrock
                              ↘ CloudWatch
```

Add authentication, input limits, rate limits, model token caps, structured logs, alarms, and a budget.

<!-- notes
Follow the request path twice: once for a static page and once for an AI request. The browser never receives AWS credentials; Lambda uses its execution role.
-->

---

## Deploy, verify, clean up

1. Verify HTTPS and private storage
2. Reject invalid and unauthenticated requests
3. Test timeouts and throttling
4. Confirm least-privilege roles
5. Check logs without storing sensitive prompts
6. Delete lab resources in every used Region

> A deployment is complete only when failure and cleanup are designed.

<!-- notes
List resources that can remain after the main compute is deleted: volumes, snapshots, load balancers, addresses, buckets, distributions, roles, or logs.
-->
