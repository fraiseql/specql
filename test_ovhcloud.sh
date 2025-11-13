#!/bin/bash
# OVHcloud Bare Metal Provisioning Script
# Generated for test-bare-metal

set -e

# Configuration
SERVER_NAME="test-bare-metal"
SERVER_MODEL="ADVANCE-2"
DATACENTER="GRA1"
OS_TEMPLATE="ubuntu2204-server_64"
SSH_KEYS="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ..."

echo "🚀 Starting OVHcloud bare metal provisioning for test-bare-metal"

# Check if OVHcloud CLI is installed
if ! command -v ovhcli &> /dev/null; then
    echo "❌ OVHcloud CLI not found. Please install it first:"
    echo "pip install ovhcli"
    exit 1
fi

# Authenticate with OVHcloud API
echo "🔐 Authenticating with OVHcloud API..."
# Note: You need to configure your OVHcloud credentials first
# ovhcli --init

# Create the server
echo "🖥️  Creating bare metal server..."
ovhcli --format json dedicated/server/provision \
    --name "$SERVER_NAME" \
    --datacenter "$DATACENTER" \
    --server-model "$SERVER_MODEL" \
    --os-template "$OS_TEMPLATE" \
    --ssh-keys "$SSH_KEYS" \
    --private-network true \
    > server_provision.json

# Extract server information
SERVER_ID=$(jq -r '.id' server_provision.json)
SERVER_IP=$(jq -r '.ip' server_provision.json)

echo "✅ Server provisioned successfully!"
echo "Server ID: $SERVER_ID"
echo "Server IP: $SERVER_IP"

# Wait for server to be ready
echo "⏳ Waiting for server to be ready..."
while true; do
    STATUS=$(ovhcli --format json dedicated/server/$SERVER_ID | jq -r '.status')
    if [ "$STATUS" = "ready" ]; then
        break
    fi
    echo "Current status: $STATUS. Waiting..."
    sleep 30
done

echo "🎉 Server is ready!"

# Configure additional services
echo "💾 Enabling backup service..."
ovhcli dedicated/server/$SERVER_ID/backup enable
echo "📊 Enabling monitoring..."
ovhcli dedicated/server/$SERVER_ID/monitoring enable

# Install additional software if containers are specified
echo "🐳 Installing Docker and configuring container..."
ssh -o StrictHostKeyChecking=no root@$SERVER_IP << 'EOF'
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
systemctl enable docker
systemctl start docker

# Run container
docker run -d \
  -p 80:80 \
  -e ENV=production \
  nginx:latest
EOF

# Configure firewall
echo "🔥 Configuring firewall..."
ovhcli dedicated/server/$SERVER_ID/firewall enable

# Add firewall rules
# Allow container port
ovhcli dedicated/server/$SERVER_ID/firewall/rule add \
    --protocol tcp \
    --port 80 \
    --source any

# SSH access (allow from anywhere for now)
ovhcli dedicated/server/$SERVER_ID/firewall/rule add \
    --protocol tcp \
    --port 22 \
    --source any

echo "🎊 Provisioning complete!"
echo "Server Details:"
echo "  Name: $SERVER_NAME"
echo "  IP: $SERVER_IP"
echo "  Model: $SERVER_MODEL"
echo "  Datacenter: $DATACENTER"
echo "  Container Port: 80"

echo ""
echo "Next steps:"
echo "1. SSH into your server: ssh root@$SERVER_IP"
echo "2. Update your DNS records to point to $SERVER_IP"
echo "3. Configure your application"
echo "4. Set up monitoring and backups"