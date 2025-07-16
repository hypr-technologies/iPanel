# iPanel - Cloud-Native Hosting Control Panel  
**Seamlessly integrated with Hypr Technologies Infrastructure**

<div align="center">
  <img src="https://hypr.tech/images/ipanel-logo.png" alt="iPanel – Cloud Control Panel Logo" width="300"/>
  <br/><br/>

  [![GitHub release](https://img.shields.io/github/release/hypr-technologies/iPanel?style=for-the-badge)](https://github.com/hypr-technologies/iPanel/releases)
  [![GitHub issues](https://img.shields.io/github/issues/hypr-technologies/iPanel?style=for-the-badge)](https://github.com/hypr-technologies/iPanel/issues)
  [![GitHub stars](https://img.shields.io/github/stars/hypr-technologies/iPanel?style=for-the-badge)](https://github.com/hypr-technologies/iPanel/stargazers)
  [![License](https://img.shields.io/github/license/hypr-technologies/iPanel?style=for-the-badge)](https://github.com/hypr-technologies/iPanel/blob/main/LICENSE)
  [![Docker Pulls](https://img.shields.io/docker/pulls/hypr/ipanel-cloud?style=for-the-badge)](https://hub.docker.com/r/hypr/ipanel-cloud)
</div>

---

## 🌩️ Cloud-Integrated Server Management  
**iPanel is the official control panel for Hypr Technologies**, providing unified management of cloud resources, applications, and infrastructure through a single intuitive interface.

```mermaid
graph TD
    A[iPanel] --> B[Hypr Technologies API]
    B --> C[Compute Instances]
    B --> D[Kubernetes Clusters]
    B --> E[Cloud Databases]
    B --> F[Storage Buckets]
    B --> G[Serverless Functions]
    A --> H[Web Terminal]
    A --> I[App Marketplace]
    A --> J[Automated Scaling]
````

---

## Key Cloud Integrations

### 🌩️ Unified Cloud Management

* **Multi-Cloud Control**: Manage AWS, GCP, Azure, and bare metal from a unified dashboard
* **Hypr Technologies API**: Native integration with Hypr Technologies infrastructure
* **Resource Orchestration**: Deploy complex stacks with one-click templates

---

### 🚀 Cloud-Optimized Deployment

```hcl
# Deploy to Hypr Technologies with Terraform
module "ipanel-cloud" {
  source  = "hypr/panel-cloud/module"
  version = "2.3.0"

  region       = "us-west2"
  cluster_size = 3
  cloud_token  = var.hyprtoken
}
```

---

### 🔌 Cloud Service Connectors

| Service                 | Status | Features                                |
| ----------------------- | ------ | --------------------------------------- |
| **Hypr Kubernetes**     | ✅      | Cluster deployment & management         |
| **Hypr DBaaS**          | ✅      | Managed PostgreSQL/MySQL/Redis          |
| **Hypr Object Storage** | ✅      | S3-compatible storage management        |
| **Hypr Serverless**     | 🔄     | Function deployment & monitoring (beta) |

---

## Getting Started with Hypr Technologies

### 1. Cloud Console Deployment

1. Log in to [Hypr Technologies Console](https://console.hypr.tech)
2. Navigate to **Marketplace → Control Panels**
3. Select "iPanel" and configure resources
4. Deploy with one click

---

### 2. CLI Installation with Cloud Auth

```bash
# Install with cloud authentication
curl -sL https://get.hypr.tech | bash -s -- \
  --token YOUR_CLOUD_TOKEN \
  --region us-west2 \
  --features kubernetes,object-storage
```

---

### 3. Docker for Cloud Edge Nodes

```bash
docker run -d \
  --name ipanel-cloud \
  -e CLOUD_TOKEN=YOUR_CLOUD_TOKEN \
  -e CLUSTER_MODE=edge \
  -p 8080:8080 \
  hypr/ipanel-cloud:latest
```

---

## Installation Troubleshooting

### Common Installation Issues

If you encounter installation failures, we provide comprehensive fix scripts:

- **Quick Fix**: `./iPanel/quick_fix.sh` - Fast resolution for immediate deployment
- **Comprehensive Fix**: `./iPanel/install_fix_comprehensive.sh` - Complete system preparation
- **Diagnostic Tool**: `./iPanel/diagnose_installation.sh` - System analysis and recommendations

For detailed troubleshooting instructions, see [INSTALLATION_FIXES.md](iPanel/INSTALLATION_FIXES.md).

### Manual Installation Steps

1. **System Requirements**: Ensure OpenSSL, Python 3.7+, and development headers are installed
2. **Dependencies**: Install all system packages (libffi-dev, python3-dev, build-essential)
3. **Python Environment**: Create clean virtual environment at `/www/server/panel/pyenv`
4. **Service Setup**: Configure `/etc/init.d/bt` service script
5. **Verification**: Test all components before deployment

---

## 📊 Cloud Features Preview

![Cloud Dashboard](https://hypr.tech/screenshots/cloud-dash.png)
*Unified view of multi-cloud resources and server metrics*

---

## 🏢 Enterprise Cloud Capabilities

* **Auto-Scaling Groups**: Dynamic resource allocation based on load
* **Cross-Cloud Backups**: Automated snapshot management
* **Cloud Cost Analytics**: Real-time spending monitoring
* **SSO Integration**: Azure AD, GitHub, Google Workspace login
* **Audit Log Streaming**: CloudTrail-compatible logs

---

## 📚 Documentation & Support

* [Installation Guide](https://docs.infuze.cloud/ipanel/installation)
* [Documentation](https://docs.infuze.cloud/ipanel/documentation)
* [User Manual](https://docs.infuze.cloud/ipanel/user-guide)
* [API Reference](https://docs.infuze.cloud/ipanel/api)
* [Configuration Guide](https://docs.infuze.cloud/ipanel/configuration)
* [Troubleshooting](https://docs.infuze.cloud/ipanel/troubleshooting)
* [Community Forum](https://github.com/hypr-technologies/iPanel/discussions)
* [Enterprise Support](https://hypr.tech/support)

---

## 📝 License

Copyright (c) 2025 Hypr Technologies
This project is licensed under the MIT License – see the [LICENSE](LICENSE) file for details.

---

## 🌐 Hypr Technologies Ecosystem

[![GitHub](https://img.shields.io/badge/GitHub-hypr--technologies/iPanel-black?style=for-the-badge&logo=github)](https://github.com/hypr-technologies/iPanel)
[![Web](https://img.shields.io/badge/Web-hypr.tech-38B2AC?style=for-the-badge)](https://hypr.tech)
[![Twitter](https://img.shields.io/badge/Twitter-@hyprtech-1DA1F2?style=for-the-badge&logo=twitter)](https://twitter.com/hyprtech)
[![Discord](https://img.shields.io/badge/Discord-Community-5865F2?style=for-the-badge&logo=discord)](https://discord.gg/hypr)
