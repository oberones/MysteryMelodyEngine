# Mystery Music Engine - Ansible Deployment

This directory contains Ansible playbooks and configuration for deploying the Mystery Music Engine to Raspberry Pi devices.

## Quick Start

1. **Install Ansible** (if not already installed):
   ```bash
   # macOS
   brew install ansible
   
   # Ubuntu/Debian
   sudo apt-get install ansible
   ```

2. **Configure your Raspberry Pi**:
   ```bash
   cd ansible
   cp inventory.example inventory
   # Edit inventory file with your Pi's IP address
   ```

3. **Deploy**:
   ```bash
   ./deploy.sh
   ```

## What the Playbook Does

### System Setup
- Updates package cache
- Installs all required system dependencies:
  - Python 3 and development tools
  - MIDI libraries (PortMIDI, ALSA, etc.)
  - Audio system libraries
  - Build tools and utilities
- Loads ALSA sequencer module and configures it to load on boot
- Adds the user to required groups (audio, dialout, plugdev)

### Project Setup
- Clones or updates the Mystery Music Engine repository
- Creates Python virtual environment
- Installs all Python dependencies
- Creates production configuration file

### Service Configuration
- Creates systemd service for auto-start on boot
- Configures logging with rotation
- Sets up health monitoring with cron job
- Applies security hardening to the service

### Monitoring
- Health check script runs every 5 minutes
- Checks service status, MIDI devices, and log file sizes
- Automatic restart if issues are detected

## Files

- `setup-mystery-music.yml` - Main Ansible playbook
- `inventory.example` - Template inventory file
- `ansible.cfg` - Ansible configuration
- `deploy.sh` - One-click deployment script
- `templates/` - Jinja2 templates for configuration files

## Configuration

### Inventory Variables

Edit `inventory` to set:
- `ansible_host` - IP address or hostname of your Raspberry Pi
- `ansible_user` - SSH user (usually 'pi')
- `midi_input_port` - Override auto-detection
- `midi_output_port` - Override auto-detection
- `log_level` - Logging verbosity

### Production Config

The playbook creates `config.production.yaml` with sensible defaults for production use:
- Conservative mutation settings
- Longer idle timeout
- Smoother transitions
- Auto MIDI port detection

## Service Management

After deployment, the service runs automatically. Manage it with:

```bash
# Check status
sudo systemctl status mystery-music

# View logs
sudo journalctl -u mystery-music -f

# Restart service
sudo systemctl restart mystery-music

# Stop service
sudo systemctl stop mystery-music

# Disable auto-start
sudo systemctl disable mystery-music
```

## Monitoring

### Health Check
The health check script runs automatically every 5 minutes and logs to `/var/log/mystery-music/health-check.log`.

Run manually:
```bash
cd ~/MysteryMelodyMachine/rpi-engine
./health-check.sh
```

### Log Files
- `/var/log/mystery-music/mystery-music.log` - Main application log
- `/var/log/mystery-music/mystery-music-error.log` - Error log
- `/var/log/mystery-music/health-check.log` - Health monitoring log

Logs are automatically rotated daily and compressed.

## Troubleshooting

### Common Issues

**Service won't start:**
```bash
sudo journalctl -u mystery-music -n 50
```

**MIDI devices not found:**
```bash
# Check USB devices
lsusb

# Check ALSA
aconnect -l

# Check permissions
groups $USER
```

**Python dependencies missing:**
```bash
cd ~/MysteryMelodyMachine/rpi-engine
source .venv/bin/activate
pip install -r requirements.txt
```

### Re-deployment

To update the code and restart:
```bash
ansible-playbook setup-mystery-music.yml --tags project,service
```

To only update system dependencies:
```bash
ansible-playbook setup-mystery-music.yml --tags system
```

## Security

The systemd service includes security hardening:
- Runs as non-root user with minimal privileges
- Restricted file system access
- Memory limits
- No new privileges allowed

## Customization

### Custom Configuration
Create `group_vars/raspberry_pi.yml` to override defaults:
```yaml
log_level: DEBUG
midi_input_port: "Teensy MIDI"
project_branch: develop
```

### Multiple Devices
Add multiple Raspberry Pi devices to the inventory:
```ini
[raspberry_pi]
mystery-pi-1 ansible_host=192.168.1.100
mystery-pi-2 ansible_host=192.168.1.101
```

Deploy to all:
```bash
ansible-playbook setup-mystery-music.yml
```

Deploy to specific device:
```bash
ansible-playbook setup-mystery-music.yml --limit mystery-pi-1
```
