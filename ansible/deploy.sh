#!/bin/bash
# Quick deployment script for Mystery Music Engine
# This script sets up Ansible and deploys to Raspberry Pi

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INVENTORY_FILE="$SCRIPT_DIR/inventory"

echo "Mystery Music Engine - Ansible Deployment"
echo "=========================================="

# Check if Ansible is installed
if ! command -v ansible-playbook &> /dev/null; then
    echo "Ansible not found. Installing Ansible..."
    
    if command -v brew &> /dev/null; then
        # macOS with Homebrew
        brew install ansible
    elif command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        sudo apt-get update
        sudo apt-get install -y ansible
    elif command -v yum &> /dev/null; then
        # RHEL/CentOS
        sudo yum install -y ansible
    else
        echo "Please install Ansible manually and run this script again"
        exit 1
    fi
fi

# Check if inventory file exists
if [ ! -f "$INVENTORY_FILE" ]; then
    echo "Creating inventory file from example..."
    cp "$SCRIPT_DIR/inventory.example" "$INVENTORY_FILE"
    echo ""
    echo "⚠️  IMPORTANT: Edit the inventory file with your Raspberry Pi details:"
    echo "   $INVENTORY_FILE"
    echo ""
    echo "Example:"
    echo "   [raspberry_pi]"
    echo "   mystery-pi ansible_host=192.168.1.100 ansible_user=pi"
    echo ""
    read -p "Press Enter after editing the inventory file..."
fi

# Test connection to Raspberry Pi
echo "Testing connection to Raspberry Pi..."
if ansible raspberry_pi -m ping; then
    echo "✓ Connection successful"
else
    echo "✗ Connection failed. Please check:"
    echo "  1. Raspberry Pi IP address in inventory file"
    echo "  2. SSH key authentication is set up"
    echo "  3. Raspberry Pi is accessible on the network"
    exit 1
fi

# Run the playbook
echo ""
echo "Starting deployment..."
ansible-playbook setup-mystery-music.yml -v

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "The Mystery Music Engine should now be running on your Raspberry Pi."
echo ""
echo "Useful commands:"
echo "  # Check service status"
echo "  ssh pi@your-pi-ip 'sudo systemctl status mystery-music'"
echo ""
echo "  # View logs"
echo "  ssh pi@your-pi-ip 'sudo journalctl -u mystery-music -f'"
echo ""
echo "  # Restart service"
echo "  ssh pi@your-pi-ip 'sudo systemctl restart mystery-music'"
echo ""
echo "  # Check MIDI devices"
echo "  ssh pi@your-pi-ip 'cd ~/MysteryMelodyMachine/rpi-engine && ./health-check.sh'"
