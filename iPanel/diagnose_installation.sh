#!/bin/bash

# iPanel Installation Diagnostic Script
# This script identifies specific issues causing installation failures

echo "============================================="
echo "iPanel Installation Diagnostic"
echo "============================================="

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_check() {
    local status=$1
    local message=$2
    if [ "$status" = "PASS" ]; then
        echo -e "${GREEN}✓ PASS${NC} $message"
    elif [ "$status" = "FAIL" ]; then
        echo -e "${RED}✗ FAIL${NC} $message"
    else
        echo -e "${YELLOW}⚠ WARN${NC} $message"
    fi
}

print_section() {
    echo -e "\n${YELLOW}=== $1 ===${NC}"
}

# 1. System Requirements Check
print_section "System Requirements"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    print_check "PASS" "Running as root"
else
    print_check "FAIL" "Must run as root"
fi

# Check OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    print_check "PASS" "OS: $NAME $VERSION_ID"
else
    print_check "FAIL" "Cannot detect OS"
fi

# Check available space
available_space=$(df / | tail -1 | awk '{print $4}')
if [ "$available_space" -gt 1000000 ]; then  # 1GB in KB
    print_check "PASS" "Available space: $(($available_space / 1024))MB"
else
    print_check "FAIL" "Insufficient disk space: $(($available_space / 1024))MB"
fi

# 2. Required System Packages
print_section "System Packages"

packages=("openssl" "python3" "python3-pip" "python3-dev" "gcc" "make" "curl" "wget" "git")

for pkg in "${packages[@]}"; do
    if command -v "$pkg" &> /dev/null; then
        version=$(eval "$pkg --version 2>/dev/null | head -1" 2>/dev/null || echo "installed")
        print_check "PASS" "$pkg: $version"
    else
        print_check "FAIL" "$pkg not installed"
    fi
done

# Check for development headers
print_section "Development Headers"

if command -v apt-get &> /dev/null; then
    dev_packages=("libssl-dev" "libffi-dev" "python3-dev" "build-essential" "pkg-config")
    for pkg in "${dev_packages[@]}"; do
        if dpkg -l | grep -q "$pkg"; then
            print_check "PASS" "$pkg installed"
        else
            print_check "FAIL" "$pkg not installed"
        fi
    done
elif command -v yum &> /dev/null; then
    dev_packages=("openssl-devel" "libffi-devel" "python3-devel" "gcc")
    for pkg in "${dev_packages[@]}"; do
        if rpm -q "$pkg" &> /dev/null; then
            print_check "PASS" "$pkg installed"
        else
            print_check "FAIL" "$pkg not installed"
        fi
    done
fi

# 3. Python Environment Check
print_section "Python Environment"

if command -v python3 &> /dev/null; then
    python_version=$(python3 --version 2>&1)
    print_check "PASS" "Python version: $python_version"
    
    # Check if venv module is available
    if python3 -c "import venv" 2>/dev/null; then
        print_check "PASS" "venv module available"
    else
        print_check "FAIL" "venv module not available"
    fi
    
    # Check pip
    if python3 -m pip --version &> /dev/null; then
        pip_version=$(python3 -m pip --version)
        print_check "PASS" "pip: $pip_version"
    else
        print_check "FAIL" "pip not available"
    fi
else
    print_check "FAIL" "Python3 not found"
fi

# 4. Directory Structure Check
print_section "Directory Structure"

panel_dir="/www/server/panel"
if [ -d "$panel_dir" ]; then
    print_check "PASS" "Panel directory exists: $panel_dir"
    
    # Check permissions
    if [ -w "$panel_dir" ]; then
        print_check "PASS" "Panel directory is writable"
    else
        print_check "FAIL" "Panel directory is not writable"
    fi
    
    # Check for existing pyenv
    if [ -d "$panel_dir/pyenv" ]; then
        print_check "WARN" "Old pyenv directory exists (should be removed)"
    else
        print_check "PASS" "No old pyenv directory"
    fi
else
    print_check "FAIL" "Panel directory does not exist: $panel_dir"
fi

# 5. Network Connectivity Check
print_section "Network Connectivity"

if curl -s --max-time 10 https://pypi.org > /dev/null; then
    print_check "PASS" "PyPI connectivity"
else
    print_check "FAIL" "Cannot connect to PyPI"
fi

if curl -s --max-time 10 https://github.com > /dev/null; then
    print_check "PASS" "GitHub connectivity"
else
    print_check "FAIL" "Cannot connect to GitHub"
fi

# 6. Specific Error Checks
print_section "Specific Issues"

# Check for cffi build requirements
if pkg-config --exists libffi 2>/dev/null; then
    print_check "PASS" "libffi pkg-config available"
else
    print_check "FAIL" "libffi pkg-config not found (causes cffi build error)"
fi

# Check for curl development headers
if pkg-config --exists libcurl 2>/dev/null; then
    print_check "PASS" "libcurl development headers available"
else
    print_check "FAIL" "libcurl development headers not found (causes pycurl build error)"
fi

# Check for OpenSSL
if [ -f /etc/ssl/openssl.cnf ] || [ -f /usr/local/ssl/openssl.cnf ]; then
    print_check "PASS" "OpenSSL configuration found"
else
    print_check "WARN" "OpenSSL configuration not in standard location"
fi

# Check for grep issues
if echo "test!" | grep -q "!"; then
    print_check "PASS" "grep handles exclamation marks correctly"
else
    print_check "FAIL" "grep has issues with exclamation marks"
fi

# 7. Memory Check
print_section "System Resources"

# Check available memory
if command -v free &> /dev/null; then
    available_mem=$(free -m | awk 'NR==2{print $7}')
    total_mem=$(free -m | awk 'NR==2{print $2}')
    if [ "$available_mem" -gt 512 ]; then
        print_check "PASS" "Available memory: ${available_mem}MB / ${total_mem}MB"
    else
        print_check "WARN" "Low memory: ${available_mem}MB / ${total_mem}MB"
    fi
fi

# Check load average
if command -v uptime &> /dev/null; then
    load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',')
    cpu_count=$(nproc)
    if (( $(echo "$load_avg < $cpu_count" | bc -l) )); then
        print_check "PASS" "Load average: $load_avg (CPUs: $cpu_count)"
    else
        print_check "WARN" "High load average: $load_avg (CPUs: $cpu_count)"
    fi
fi

# 8. Recommendations
print_section "Recommendations"

echo "Based on the diagnostic results, here are the recommended actions:"
echo ""
echo "1. If system packages are missing, install them:"
echo "   Ubuntu/Debian: apt-get install openssl libssl-dev libffi-dev python3-dev build-essential pkg-config libcurl4-openssl-dev"
echo "   CentOS/RHEL: yum install openssl openssl-devel libffi-devel python3-devel gcc curl-devel"
echo ""
echo "2. If Python environment issues exist:"
echo "   - Remove old pyenv: rm -rf /www/server/panel/pyenv"
echo "   - Create new environment: python3 -m venv /www/server/panel/pyenv"
echo ""
echo "3. For build issues:"
echo "   - Install development headers and build tools"
echo "   - Check network connectivity to PyPI"
echo "   - Consider using system packages for problematic dependencies"
echo ""
echo "4. Run the comprehensive fix script: ./install_fix_comprehensive.sh"

echo ""
echo "============================================="
echo "Diagnostic completed"
echo "============================================="
