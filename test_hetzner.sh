#!/bin/bash
# Hetzner Cloud Provisioning Script
# Generated for test-bare-metal

set -e

# Configuration
SERVER_NAME="test-bare-metal"
SERVER_TYPE="ADVANCE-2"
DATACENTER="GRA1"
IMAGE="ubuntu-22.04"
SSH_KEYS="ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ..."

echo "🚀 Starting Hetzner Cloud provisioning for test-bare-metal"

# Check if hcloud CLI is installed
if ! command -v hcloud &> /dev/null; then
    echo "❌ Hetzner Cloud CLI not found. Please install it first:"
    echo "curl -fsSL https://github.com/hetznercloud/cli/releases/latest/download/hcloud-linux-amd64.tar.gz | tar -xzv"
    echo "sudo mv hcloud /usr/local/bin/"
    exit 1
fi

# Authenticate with Hetzner Cloud API
echo "🔐 Authenticating with Hetzner Cloud API..."
# Note: You need to configure your Hetzner Cloud token first
# hcloud context create specql

# Create SSH key if provided
echo "🔑 Adding SSH keys..."
for key in ${SSH_KEYS//,/ }; do
    KEY_NAME="key-$(echo $key | cut -d' ' -f3)"
    hcloud ssh-key create --name "$KEY_NAME" --public-key "$key" || true
done

# Create the server
echo "🖥️  Creating cloud server..."
CREATE_CMD="hcloud server create --name $SERVER_NAME --type $SERVER_TYPE --image $IMAGE --location $DATACENTER"
CREATE_CMD="$CREATE_CMD --ssh-key ${SSH_KEYS//, / --ssh-key }"

# Execute server creation
eval $CREATE_CMD > server_create.json

# Extract server information
SERVER_ID=$(cat server_create.json | grep -o '"id":[0-9]*' | cut -d':' -f2)
SERVER_IP=$(hcloud server describe $SERVER_NAME -o json | jq -r '.public_net.ipv4.ip')

echo "✅ Server created successfully!"
echo "Server ID: $SERVER_ID"
echo "Server IP: $SERVER_IP"

# Wait for server to be ready
echo "⏳ Waiting for server to be ready..."
while true; do
    STATUS=$(hcloud server describe $SERVER_NAME -o json | jq -r '.status')
    if [ "$STATUS" = "running" ]; then
        break
    fi
    echo "Current status: $STATUS. Waiting..."
    sleep 10
done

echo "🎉 Server is ready!"

# Configure additional services
echo "💾 Enabling backup service..."
# Note: Hetzner backup service needs to be configured manually or via API
echo "Hetzner backup service requires manual configuration via web interface"
echo "📊 Enabling monitoring..."
# Install basic monitoring
ssh -o StrictHostKeyChecking=no root@$SERVER_IP << 'EOF'
# Install monitoring tools
apt-get update
apt-get install -y htop iotop sysstat

# Install Node Exporter for Prometheus (optional)
wget https://github.com/prometheus/node_exporter/releases/download/v1.5.0/node_exporter-1.5.0.linux-amd64.tar.gz
tar xvf node_exporter-1.5.0.linux-amd64.tar.gz
mv node_exporter-1.5.0.linux-amd64/node_exporter /usr/local/bin/
rm -rf node_exporter-1.5.0.linux-amd64*

# Create systemd service for Node Exporter
cat > /etc/systemd/system/node_exporter.service << 'SERVICEEOF'
[Unit]
Description=Node Exporter
Wants=network-online.target
After=network-online.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
SERVICEEOF

useradd -rs /bin/false node_exporter
systemctl daemon-reload
systemctl enable node_exporter
systemctl start node_exporter
EOF

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
hcloud firewall create --name "$SERVER_NAME-firewall"

# Add firewall rules
# Allow container port
hcloud firewall add-rule "$SERVER_NAME-firewall" \
    --direction in \
    --protocol tcp \
    --port 80 \
    --source-ips 0.0.0.0/0 \
    --description "Container port"

# SSH access (allow from anywhere for now)
hcloud firewall add-rule "$SERVER_NAME-firewall" \
    --direction in \
    --protocol tcp \
    --port 22 \
    --source-ips 0.0.0.0/0 \
    --description "SSH access"

# Apply firewall to server
hcloud server add-to-firewall "$SERVER_NAME" "$SERVER_NAME-firewall"

echo "🎊 Provisioning complete!"
echo "Server Details:"
echo "  Name: $SERVER_NAME"
echo "  IP: $SERVER_IP"
echo "  Type: $SERVER_TYPE"
echo "  Location: $DATACENTER"
echo "  Container Port: 80"

echo ""
echo "Next steps:"
echo "1. SSH into your server: ssh root@$SERVER_IP"
echo "2. Update your DNS records to point to $SERVER_IP"
echo "3. Configure your application"
echo "4. Set up monitoring and backups"