# Installation Guide

This guide will walk you through the installation process for iPanel on various platforms.

## System Requirements

Before installing iPanel, ensure your system meets the following requirements:

### Minimum Requirements
- **OS**: Ubuntu 20.04+, CentOS 8+, Debian 11+, or Rocky Linux 8+
- **CPU**: 2 cores
- **RAM**: 4GB
- **Storage**: 20GB free space
- **Network**: Internet connection for initial setup

### Recommended Requirements
- **OS**: Ubuntu 22.04 LTS
- **CPU**: 4 cores
- **RAM**: 8GB
- **Storage**: 50GB SSD
- **Network**: Stable internet connection

## Installation Methods

### Method 1: Quick Install Script (Recommended)

The easiest way to install iPanel is using our automated installation script:

```bash
# Download and run the installation script
curl -sSL https://install.hypr.tech/ipanel | bash

# For custom installation options
curl -sSL https://install.hypr.tech/ipanel | bash -s -- --version=8.0.0 --port=8080
```

### Method 2: Docker Installation

Deploy iPanel using Docker for containerized environments:

```bash
# Pull the latest iPanel image
docker pull hypr-technologies/ipanel:latest

# Run iPanel container
docker run -d \
  --name ipanel \
  --restart=unless-stopped \
  -p 8080:8080 \
  -v /var/lib/ipanel:/data \
  hypr-technologies/ipanel:latest
```

### Method 3: Docker Compose

For production deployments, use Docker Compose:

```yaml
version: '3.8'

services:
  ipanel:
    image: hypr-technologies/ipanel:latest
    container_name: ipanel
    restart: unless-stopped
    ports:
      - "8080:8080"
    volumes:
      - ipanel_data:/data
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - IPANEL_PORT=8080
      - IPANEL_SSL=false

volumes:
  ipanel_data:
```

### Method 4: Manual Installation

For advanced users who want full control over the installation process:

1. **Download the latest release**
   ```bash
   wget https://github.com/hypr-technologies/iPanel/releases/latest/download/ipanel-linux-amd64.tar.gz
   tar -xzf ipanel-linux-amd64.tar.gz
   ```

2. **Create system user**
   ```bash
   sudo useradd -r -s /bin/false ipanel
   sudo mkdir -p /opt/ipanel
   sudo chown ipanel:ipanel /opt/ipanel
   ```

3. **Install dependencies**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install -y python3 python3-pip nginx

   # CentOS/RHEL
   sudo yum install -y python3 python3-pip nginx
   ```

4. **Configure and start iPanel**
   ```bash
   sudo cp ipanel /opt/ipanel/
   sudo chmod +x /opt/ipanel/ipanel
   sudo systemctl enable ipanel
   sudo systemctl start ipanel
   ```

## Post-Installation Configuration

### 1. Initial Setup

After installation, access the web interface at `http://your-server-ip:8080` and complete the initial setup:

1. Create the admin user account
2. Configure basic settings
3. Set up SSL certificates (recommended)
4. Configure firewall rules

### 2. Security Configuration

For production environments, follow these security best practices:

```bash
# Change default port
sudo nano /opt/ipanel/config/app.conf

# Set up SSL
sudo certbot --nginx -d your-domain.com

# Configure firewall
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. Database Setup

iPanel supports multiple database backends:

```bash
# Install MySQL (recommended)
sudo apt install -y mysql-server
sudo mysql_secure_installation

# Configure database connection
sudo nano /opt/ipanel/config/database.conf
```

## Verification

Verify your installation by checking:

1. **Service Status**
   ```bash
   sudo systemctl status ipanel
   ```

2. **Web Interface**
   - Open `http://your-server-ip:8080`
   - Login with admin credentials
   - Check dashboard for system status

3. **Logs**
   ```bash
   sudo journalctl -u ipanel -f
   ```

## Updating iPanel

To update iPanel to the latest version:

```bash
# Using the update script
curl -sSL https://install.hypr.tech/ipanel-update | bash

# Or manually
sudo systemctl stop ipanel
sudo cp /path/to/new/ipanel /opt/ipanel/ipanel
sudo systemctl start ipanel
```

## Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   sudo lsof -i :8080
   sudo kill -9 <PID>
   ```

2. **Permission errors**
   ```bash
   sudo chown -R ipanel:ipanel /opt/ipanel
   sudo chmod +x /opt/ipanel/ipanel
   ```

3. **Service won't start**
   ```bash
   sudo journalctl -u ipanel -n 50
   ```

For more troubleshooting information, see the [Troubleshooting Guide](troubleshooting.md).

## Next Steps

After successful installation:

1. [Configure iPanel](configuration.md)
2. [Set up SSL certificates](ssl.md)
3. [Configure backups](backup.md)
4. [Review security settings](security.md)

---

**Need Help?**
- [Community Forum](https://forum.hypr.tech)
- [GitHub Issues](https://github.com/hypr-technologies/iPanel/issues)
- [Documentation](https://docs.infuze.cloud/ipanel)
