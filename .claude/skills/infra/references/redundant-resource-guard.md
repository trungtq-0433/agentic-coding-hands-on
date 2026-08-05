# Redundant Resource Guard

Common cases where the LLM adds overlapping AWS resources that serve the same function.
Do NOT generate both sides unless the user explicitly requests it.

## Overlapping Resource Pairs

| If generating... | Do NOT also add... | Why |
|------------------|--------------------|-----|
| ALB + ECS/EKS | API Gateway (HTTP/REST) | ALB already handles routing; API GW is redundant |
| CloudFront + ALB | Second ALB or NLB | CloudFront is the edge; one LB behind it suffices |
| API Gateway + Lambda | ALB | API GW already routes to Lambda |
| NAT Gateway | VPC Endpoint for S3/DynamoDB | Add endpoints only if user mentions cost optimization |
| Route53 + ALB | Elastic IP on ALB | ALB DNS is the standard pattern |
| SQS between services | SNS + SQS fan-out | Only add fan-out if multiple consumers are shown |
| ECS + ALB | NLB | Use NLB only for non-HTTP (TCP/UDP) traffic |
| CloudFront + S3 | S3 website hosting config | CloudFront serves; S3 website endpoint not needed |

## Decision Rule

**If a resource isn't in the user's request or Mermaid diagram, don't add it.**
When unsure, ask: "Should I also include [resource]? It would add [benefit] but overlaps with [existing]."

## Review Checklist

When reviewing generated Terraform (create, generate, or review):

1. List all resource types in the output
2. Check each pair against the table above
3. If overlap found:
   - Flag in security review as **LOW** severity: "Redundant resource: [X] overlaps with [Y]"
   - Recommend removal unless user confirms both are needed
4. Check cost estimate — redundant resources inflate the estimate unnecessarily
