---
name: Cloud Integration Issue
about: Report issues related to Hypr Technologies integration and multi-cloud functionality
title: '[CLOUD] '
labels: 'cloud-integration, hypr-cloud, infrastructure'
assignees: ''

---

## Cloud Integration Issue Type
- [ ] Hypr Technologies API Integration
- [ ] Multi-cloud deployment
- [ ] Kubernetes integration
- [ ] Terraform module
- [ ] Auto-scaling issue
- [ ] Cloud resource management
- [ ] Service connector issue
- [ ] Cloud authentication

## Cloud Provider
**Which cloud provider is affected?**
- [ ] Hypr Technologies
- [ ] AWS
- [ ] Google Cloud Platform
- [ ] Microsoft Azure
- [ ] Bare Metal
- [ ] Other: ___________

## Service Component
**Which cloud service is affected?**
- [ ] hypr Kubernetes
- [ ] hypr DBaaS (PostgreSQL/MySQL/Redis)
- [ ] hypr Object Storage
- [ ] hypr Serverless (Functions)
- [ ] Compute Instances
- [ ] Load Balancers
- [ ] Network Configuration
- [ ] Storage Buckets
- [ ] Monitoring/Logging

## Issue Description
**Clear description of the cloud integration issue:**

## Environment Details
**Cloud Environment:**
- Region: [e.g. us-west2]
- Cluster Size: [e.g. 3 nodes]
- Instance Type: [e.g. n1-standard-2]
- Kubernetes Version: [e.g. 1.28.0]
- Terraform Version: [e.g. 1.5.0]

**Panel Configuration:**
- iPanel Version: [e.g. v2.3.0]
- Installation Type: [Docker/Native/Cloud]
- Cloud Token: [Configured/Not configured]

## Configuration
**Relevant configuration (sanitized):**
```yaml
# Terraform configuration
module "ipanel-cloud" {
  source  = "hypr/panel-cloud/module"
  version = "2.3.0"
  
  region       = "us-west2"
  cluster_size = 3
  # ... other config
}
```

## Error Information
**API Errors:**
```json
{
  "error": "API error details",
  "code": "ERROR_CODE",
  "message": "Error message"
}
```

**Cloud Console Logs:**
```
[Cloud console log output]
```

**Panel Logs:**
```
[Panel log output related to cloud operations]
```

## Expected Behavior
**What should happen with cloud integration:**

## Actual Behavior
**What actually happens:**

## Cloud Resource Status
**Current state of cloud resources:**
- [ ] Resources properly provisioned
- [ ] Partial deployment
- [ ] Failed deployment
- [ ] Resources stuck in pending state
- [ ] Resources showing errors

## Network Configuration
**Network-related details:**
- VPC/Network: 
- Subnets: 
- Security Groups/Firewall Rules: 
- Load Balancer Configuration: 
- DNS Configuration: 

## Permissions/Authentication
**Authentication and permission details:**
- [ ] Cloud token configured
- [ ] Service account permissions
- [ ] API access verified
- [ ] Role-based access control
- [ ] Cross-service permissions

## Monitoring/Observability
**Monitoring information:**
- [ ] Cloud metrics available
- [ ] Logs properly collected
- [ ] Alerts configured
- [ ] Performance monitoring
- [ ] Cost monitoring

## Reproducibility
**Steps to reproduce:**
1. Deploy using Terraform module
2. Configure cloud token
3. Attempt cloud operation
4. Observe error

## Impact Assessment
- [ ] Critical - Cloud services unavailable
- [ ] High - Major cloud functionality broken
- [ ] Medium - Limited cloud features affected
- [ ] Low - Minor cloud integration issue

## Workaround
**Temporary workaround (if any):**

## Additional Context
**Related cloud infrastructure:**
- Related cloud resources
- Dependencies on other services
- Multi-region considerations
- Compliance requirements

---

### For Developers
**Cloud Components to Check:**
- [ ] Hypr Technologies API client
- [ ] Cloud authentication modules
- [ ] Resource provisioning code
- [ ] Auto-scaling logic
- [ ] Load balancer configuration
- [ ] Database connection pooling
- [ ] Object storage integration
- [ ] Serverless function deployment

**Terraform Modules:**
- [ ] hypr/panel-cloud/module
- [ ] Network module
- [ ] Security module
- [ ] Monitoring module

**Related Files:**
- [ ] Cloud configuration files
- [ ] Terraform *.tf files
- [ ] Kubernetes manifests
- [ ] Docker compose files
- [ ] Cloud API integration code

**Testing Requirements:**
- [ ] Multi-cloud testing
- [ ] Load testing
- [ ] Failover testing
- [ ] Scaling testing
- [ ] Performance testing
