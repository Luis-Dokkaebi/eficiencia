#!/bin/bash
# install.sh - Install Tracking System on Linux

set -e

APP_NAME="tracking-system"
INSTALL_DIR="/opt/$APP_NAME"
BIN_NAME="TrackingSystem" # Matches name in .spec file

echo "🔍 Checking for Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found."
    echo "Please install Docker from https://docs.docker.com/engine/install/"
    exit 1
fi

echo "🔍 Checking for Docker Compose..."
if ! docker compose version &> /dev/null && ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found."
    exit 1
fi

echo "📦 Installing $APP_NAME to $INSTALL_DIR..."

# Create install directory
sudo mkdir -p "$INSTALL_DIR"
sudo chown -R $USER:$USER "$INSTALL_DIR"

# Copy binary (OneFile Mode)
if [ -f "dist/$BIN_NAME" ]; then
    echo "Copying binary..."
    cp "dist/$BIN_NAME" "$INSTALL_DIR/$BIN_NAME"
    chmod +x "$INSTALL_DIR/$BIN_NAME"
else
    echo "❌ Binary not found in dist/$BIN_NAME."
    echo "Please build it first with: pyinstaller tracking_system.spec"
    exit 1
fi

# Copy config and compose if present in root
if [ ! -f "$INSTALL_DIR/.env" ]; then
    if [ -f ".env" ]; then
        cp .env "$INSTALL_DIR/.env"
    elif [ -f ".env.example" ]; then
        cp .env.example "$INSTALL_DIR/.env"
    fi
fi

if [ -f "docker-compose.yml" ]; then
    cp docker-compose.yml "$INSTALL_DIR/"
fi

# Ensure data directories exist
mkdir -p "$INSTALL_DIR/data/faces"
mkdir -p "$INSTALL_DIR/data/zonas"
mkdir -p "$INSTALL_DIR/data/snapshots"

# Start DB
echo "🗄️  Starting Database Service via Docker Compose..."
cd "$INSTALL_DIR"
if grep -q "db:" docker-compose.yml; then
    docker compose up -d db || docker-compose up -d db
else
    echo "⚠️  'db' service not found in docker-compose.yml. Skipping DB start."
fi

# Setup Systemd Service
SERVICE_FILE="/etc/systemd/system/$APP_NAME.service"

echo "⚙️  Creating Service File at $SERVICE_FILE..."
sudo bash -c "cat <<EOF > $SERVICE_FILE
[Unit]
Description=Tracking System Service
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
WorkingDirectory=$INSTALL_DIR
ExecStart=$INSTALL_DIR/$BIN_NAME
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF"

# Reload Daemon
sudo systemctl daemon-reload
sudo systemctl enable $APP_NAME
sudo systemctl restart $APP_NAME

echo "✅ Installation Complete. Service started."
echo "Check logs with: sudo journalctl -u $APP_NAME -f"
