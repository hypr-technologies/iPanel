#!/bin/bash

# iPanel Comprehensive Installation Fix
# This script fixes all identified issues from the installation logs

set -e  # Exit on any error

echo "============================================="
echo "iPanel Installation Fix - Comprehensive"
echo "============================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root"
   exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$NAME
    VERSION=$VERSION_ID
elif [ -f /etc/redhat-release ]; then
    OS="Red Hat"
    VERSION=$(cat /etc/redhat-release | grep -oE '[0-9]+\.[0-9]+' | cut -d. -f1)
elif [ -f /etc/debian_version ]; then
    OS="Debian"
    VERSION=$(cat /etc/debian_version)
else
    print_error "Cannot detect OS"
    exit 1
fi

print_status "Detected OS: $OS $VERSION"

# 1. Install system dependencies
print_status "Installing system dependencies..."

if command -v apt-get &> /dev/null; then
    # Ubuntu/Debian
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -y
    apt-get install -y \
        openssl \
        libssl-dev \
        libffi-dev \
        python3-dev \
        python3-pip \
        python3-venv \
        build-essential \
        pkg-config \
        libcurl4-openssl-dev \
        libgnutls28-dev \
        libc6-dev \
        gcc \
        g++ \
        make \
        zlib1g-dev \
        libxml2-dev \
        libxslt1-dev \
        libjpeg-dev \
        libpng-dev \
        curl \
        wget \
        git \
        unzip \
        vim \
        net-tools \
        lsof \
        psmisc
        
elif command -v yum &> /dev/null; then
    # CentOS/RHEL
    yum update -y
    yum install -y \
        openssl \
        openssl-devel \
        libffi-devel \
        python3-devel \
        python3-pip \
        gcc \
        gcc-c++ \
        make \
        zlib-devel \
        libxml2-devel \
        libxslt-devel \
        libjpeg-devel \
        libpng-devel \
        curl-devel \
        wget \
        git \
        unzip \
        vim \
        net-tools \
        lsof \
        psmisc
        
elif command -v apk &> /dev/null; then
    # Alpine Linux
    apk update
    apk add --no-cache \
        openssl \
        openssl-dev \
        libffi-dev \
        python3-dev \
        py3-pip \
        build-base \
        pkgconfig \
        curl-dev \
        zlib-dev \
        libxml2-dev \
        libxslt-dev \
        jpeg-dev \
        libpng-dev \
        curl \
        wget \
        git \
        unzip \
        vim \
        net-tools \
        lsof \
        psmisc
else
    print_error "Unsupported package manager"
    exit 1
fi

# 2. Fix OpenSSL library path issues
print_status "Configuring OpenSSL library paths..."
if [ -d "/usr/local/openssl111" ]; then
    export LD_LIBRARY_PATH=/usr/local/openssl111/lib:$LD_LIBRARY_PATH
    echo 'export LD_LIBRARY_PATH=/usr/local/openssl111/lib:$LD_LIBRARY_PATH' >> /etc/profile
fi

# 3. Create and set up panel directory structure
print_status "Setting up panel directory structure..."
PANEL_DIR="/www/server/panel"
mkdir -p "$PANEL_DIR"
mkdir -p "$PANEL_DIR/logs"
mkdir -p "$PANEL_DIR/data"
mkdir -p "$PANEL_DIR/config"
mkdir -p "$PANEL_DIR/tmp"
mkdir -p "$PANEL_DIR/script"
mkdir -p "$PANEL_DIR/class"
mkdir -p "$PANEL_DIR/BTPanel"

# 4. Remove old problematic Python environment
print_status "Removing old Python environment..."
if [ -d "$PANEL_DIR/pyenv" ]; then
    rm -rf "$PANEL_DIR/pyenv"
fi

# 5. Create new Python virtual environment
print_status "Creating new Python virtual environment..."
cd "$PANEL_DIR"
python3 -m venv pyenv

# Activate virtual environment
source pyenv/bin/activate

# 6. Upgrade pip and essential packages
print_status "Upgrading pip and essential packages..."
pip install --upgrade pip
pip install --upgrade setuptools wheel

# 7. Install Python dependencies with error handling
print_status "Installing Python dependencies..."

# Install dependencies one by one with error handling
DEPS=(
    "psutil==5.9.5"
    "bcrypt==4.0.1"
    "cachelib==0.12.0"
    "Flask==2.2.5"
    "Flask-Session==0.4.0"
    "Werkzeug==2.2.3"
    "requests==2.31.0"
    "paramiko==3.4.0"
    "cryptography==40.0.2"
    "gevent==24.2.1"
    "Jinja2==3.1.3"
    "click==8.1.7"
    "itsdangerous==2.1.2"
    "MarkupSafe==2.1.5"
    "configobj==5.0.8"
    "supervisor==4.2.5"
    "PyMySQL==1.0.3"
    "redis==4.5.4"
    "pymongo==4.6.3"
    "pillow==10.3.0"
    "docker==6.0.1"
    "peewee==3.16.2"
    "six==1.16.0"
    "pytz==2023.3"
    "charset-normalizer==3.3.2"
    "certifi==2024.2.2"
    "urllib3==1.26.18"
    "idna==3.7"
    "cffi==1.15.1"
    "pycparser==2.21"
    "PyNaCl==1.5.0"
    "pyOpenSSL==23.1.1"
    "future==0.18.3"
    "beautifulsoup4==4.12.2"
    "lxml==5.0.0"
    "PyYAML==6.0.1"
    "toml==0.10.2"
    "packaging==23.1"
    "typing-extensions==4.7.1"
    "importlib-metadata==6.7.0"
    "zipp==3.15.0"
    "decorator==5.1.1"
    "greenlet==3.0.3"
    "async-timeout==4.0.3"
    "dnspython==2.3.0"
    "chardet==5.1.0"
    "Cython==0.29.34"
    "enum34==1.1.10"
    "IPy==1.1"
    "natsort==8.4.0"
    "protobuf==4.22.3"
    "Pygments==2.15.1"
    "pyparsing==3.0.9"
    "PySocks==1.7.1"
    "qrcode==7.4.2"
    "simple-websocket==0.10.0"
    "soupsieve==2.4.1"
    "SQLAlchemy==2.0.10"
    "Flask-SQLAlchemy==3.0.3"
    "websocket-client==1.5.1"
    "wheel==0.38.1"
    "wsproto==1.2.0"
    "xmltodict==0.13.0"
    "zope.event==5.0"
    "zope.interface==6.2"
    "flask-sock==0.7.0"
    "gevent-websocket==0.10.1"
    "h11==0.14.0"
    "pandas==2.2.2"
    "Brotli==1.1.0"
    "rarfile==4.2"
    "pyotp==2.9.0"
    "ntplib==0.4.0"
    "distro==1.9.0"
)

# Install core dependencies first
for dep in "${DEPS[@]}"; do
    print_status "Installing $dep..."
    if ! pip install "$dep"; then
        print_warning "Failed to install $dep, continuing..."
    fi
done

# Try to install pycurl with special handling
print_status "Installing pycurl with special handling..."
export PYCURL_SSL_LIBRARY=openssl
if ! pip install "pycurl>=7.45.2,<8.0.0"; then
    print_warning "Failed to install pycurl, trying alternative method..."
    if command -v apt-get &> /dev/null; then
        apt-get install -y python3-pycurl
    elif command -v yum &> /dev/null; then
        yum install -y python3-pycurl
    fi
fi

# 8. Fix init.sh script issues
print_status "Fixing init.sh script..."
if [ -f "/volume/iPanel/init.sh" ]; then
    # Fix grep warning issues
    sed -i 's/\\!/!/g' /volume/iPanel/init.sh
    cp /volume/iPanel/init.sh "$PANEL_DIR/init.sh"
elif [ -f "$PANEL_DIR/init.sh" ]; then
    sed -i 's/\\!/!/g' "$PANEL_DIR/init.sh"
fi

# 9. Fix tools.py Python path
print_status "Fixing tools.py Python path..."
if [ -f "$PANEL_DIR/tools.py" ]; then
    sed -i "1i#!/www/server/panel/pyenv/bin/python3" "$PANEL_DIR/tools.py"
    chmod +x "$PANEL_DIR/tools.py"
fi

# 10. Create init service script
print_status "Creating init service script..."
cat > /etc/init.d/bt << 'EOF'
#!/bin/bash
# iPanel service script

. /etc/rc.d/init.d/functions

USER="root"
DAEMON="iPanel"
ROOT_DIR="/www/server/panel"

SERVER="$ROOT_DIR/pyenv/bin/python3"
LOCK_FILE="/var/lock/subsys/bt"

do_start() {
    if [ ! -f "$LOCK_FILE" ] ; then
        echo -n "Starting $DAEMON: "
        runuser -l "$USER" -c "$SERVER" && echo_success || echo_failure
        RETVAL=$?
        echo
        [ $RETVAL -eq 0 ] && touch $LOCK_FILE
    else
        echo "$DAEMON is locked."
    fi
}
do_stop() {
    echo -n $"Shutting down $DAEMON: "
    pid=$(ps -aefw | grep "$DAEMON" | grep -v " grep " | awk '{print $2}')
    kill -9 $pid > /dev/null 2>&1
    [ $? -eq 0 ] && echo_success || echo_failure
    echo
    rm -f $LOCK_FILE
}

case "$1" in
    start)
        do_start
        ;;
    stop)
        do_stop
        ;;
    restart)
        do_stop
        do_start
        ;;
    *)
        echo "Usage: $0 {start|stop|restart}"
        RETVAL=1
esac

exit $RETVAL
EOF

chmod +x /etc/init.d/bt

# 11. Create default configuration files
print_status "Creating default configuration files..."

# Create port configuration
echo "8888" > "$PANEL_DIR/data/port.pl"

# Create basic panel configuration
cat > "$PANEL_DIR/config/config.json" << 'EOF'
{
    "port": 8888,
    "ssl": false,
    "debug": false,
    "panel_path": "/www/server/panel",
    "server_path": "/www/server",
    "setup_path": "/www/server/panel"
}
EOF

# Create empty admin configuration
cat > "$PANEL_DIR/data/admin_path.pl" << 'EOF'
/
EOF

# 12. Set proper permissions
print_status "Setting proper permissions..."
chown -R root:root "$PANEL_DIR"
chmod -R 755 "$PANEL_DIR"
chmod +x "$PANEL_DIR/init.sh" 2>/dev/null || true
chmod +x "$PANEL_DIR/BT-Panel" 2>/dev/null || true
chmod +x "$PANEL_DIR/BT-Task" 2>/dev/null || true

# 13. Create log files
print_status "Creating log files..."
touch "$PANEL_DIR/logs/error.log"
touch "$PANEL_DIR/logs/task.log"
touch "$PANEL_DIR/logs/panel.log"
chmod 666 "$PANEL_DIR/logs/"*.log

# 14. Test Python environment
print_status "Testing Python environment..."
cd "$PANEL_DIR"
if "$PANEL_DIR/pyenv/bin/python3" -c "import psutil, bcrypt, flask; print('Python environment is working')"; then
    print_status "Python environment test passed"
else
    print_error "Python environment test failed"
    exit 1
fi

# 15. Create startup script
print_status "Creating startup script..."
cat > "$PANEL_DIR/start.sh" << 'EOF'
#!/bin/bash
cd /www/server/panel
export LD_LIBRARY_PATH=/usr/local/openssl111/lib:$LD_LIBRARY_PATH
source pyenv/bin/activate
python3 runserver.py
EOF

chmod +x "$PANEL_DIR/start.sh"

# 16. Final system configuration
print_status "Final system configuration..."

# Disable SELinux if it exists
if command -v setenforce &> /dev/null; then
    setenforce 0 2>/dev/null || true
fi

# Configure firewall if needed
if command -v ufw &> /dev/null; then
    ufw allow 8888/tcp
elif command -v firewall-cmd &> /dev/null; then
    firewall-cmd --permanent --add-port=8888/tcp
    firewall-cmd --reload
fi

print_status "Installation fix completed successfully!"
echo "============================================="
echo -e "${GREEN}Next steps:${NC}"
echo "1. Copy your iPanel source code to $PANEL_DIR"
echo "2. Run: cd $PANEL_DIR && ./start.sh"
echo "3. Access the panel at: http://your-server-ip:8888"
echo "============================================="
