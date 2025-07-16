#!/bin/bash

# Quick Fix for iPanel Installation Issues
# This script addresses the most common problems from your error logs

echo "===========================================" 
echo "iPanel Quick Fix Script"
echo "==========================================="

# Must run as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (sudo)"
   exit 1
fi

# 1. Install missing system dependencies
echo "Step 1: Installing system dependencies..."
if command -v apt-get &> /dev/null; then
    apt-get update
    apt-get install -y openssl libssl-dev libffi-dev python3-dev build-essential pkg-config libcurl4-openssl-dev
elif command -v yum &> /dev/null; then
    yum install -y openssl openssl-devel libffi-devel python3-devel gcc curl-devel
fi

# 2. Create clean Python environment
echo "Step 2: Creating clean Python environment..."
PANEL_DIR="/www/server/panel"
mkdir -p "$PANEL_DIR"
cd "$PANEL_DIR"

# Remove old broken environment
if [ -d "pyenv" ]; then
    rm -rf pyenv
fi

# Create new environment
python3 -m venv pyenv
source pyenv/bin/activate

# 3. Install core Python packages
echo "Step 3: Installing core Python packages..."
pip install --upgrade pip setuptools wheel

# Install critical packages first
pip install psutil==5.9.5
pip install bcrypt==4.0.1
pip install Flask==2.2.5
pip install requests==2.31.0
pip install cachelib==0.12.0

# 4. Fix the tools.py import issue
echo "Step 4: Fixing tools.py import issue..."
if [ -f "$PANEL_DIR/tools.py" ]; then
    # Add proper shebang
    sed -i '1i#!/www/server/panel/pyenv/bin/python3' "$PANEL_DIR/tools.py"
    chmod +x "$PANEL_DIR/tools.py"
fi

# 5. Create basic configuration
echo "Step 5: Creating basic configuration..."
mkdir -p "$PANEL_DIR/data"
echo "8888" > "$PANEL_DIR/data/port.pl"

# 6. Fix /etc/init.d/bt script
echo "Step 6: Creating service script..."
cat > /etc/init.d/bt << 'EOF'
#!/bin/bash
# iPanel service script

PANEL_DIR="/www/server/panel"
PYTHON_BIN="$PANEL_DIR/pyenv/bin/python3"

case "$1" in
    start)
        echo "Starting iPanel..."
        cd "$PANEL_DIR"
        source pyenv/bin/activate
        nohup python3 runserver.py > logs/panel.log 2>&1 &
        echo "iPanel started"
        ;;
    stop)
        echo "Stopping iPanel..."
        pkill -f "python3 runserver.py"
        echo "iPanel stopped"
        ;;
    restart)
        $0 stop
        sleep 2
        $0 start
        ;;
    *)
        echo "Usage: $0 {start|stop|restart}"
        exit 1
        ;;
esac
EOF

chmod +x /etc/init.d/bt

# 7. Test the environment
echo "Step 7: Testing Python environment..."
if "$PANEL_DIR/pyenv/bin/python3" -c "import psutil, bcrypt, flask; print('SUCCESS: Core packages working')"; then
    echo "✓ Python environment test passed"
else
    echo "✗ Python environment test failed"
    exit 1
fi

echo "==========================================="
echo "Quick fix completed!"
echo ""
echo "Next steps:"
echo "1. Copy your iPanel files to /www/server/panel"
echo "2. Run: /etc/init.d/bt start"
echo "3. Check logs: tail -f /www/server/panel/logs/panel.log"
echo "==========================================="
