# Mystery Melody Machine - Ansible Deployment

This directory contains Ansible playbooks for deploying the Mystery Melody Machine to Raspberry Pi devices, with specialized support for **Zynthian v4 hardware**.

## Quick Start

### Standard Raspberry Pi
```bash
# 1. Install Ansible
brew install ansible  # macOS
sudo apt-get install ansible  # Ubuntu/Debian

# 2. Configure inventory
cd ansible
cp inventory.example inventory
# Edit inventory with your Pi's IP

# 3. Deploy
./deploy.sh
```

### Zynthian v4 Hardware 🎛️
```bash
# 1. Setup for Zynthian hardware
cd ansible
cp inventory.example inventory
# Edit inventory - add your Pi to [zynthian_hardware] group

# 2. Deploy with Zynthian support
ansible-playbook -i inventory setup-zynthian.yml

# 3. Test hardware controls
ssh pi@your-zynthian-pi
cd /opt/MysteryMelodyEngine/rpi-engine
./check-zynthian-hardware.sh
```

## Zynthian v4 Hardware Support 🎛️

The playbooks now include full support for Zynthian v4 hardware:

### Hardware Features
- **4 Rotary Encoders** with push buttons for real-time control
- **4 Push Buttons** for triggering actions
- **Built-in MIDI DIN** connectors (no USB needed)
- **GPIO-based** hardware interface
- **Low-latency** performance optimizations

### Control Mapping
- **Encoder 0**: MIDI Input Channel (1-16) • *Push: Reset to 1*
- **Encoder 1**: MIDI Output Channel (1-16) • *Push: Reset to 1*
- **Encoder 2**: CC Profile cycling • *Push: Reset to first*
- **Encoder 3**: BPM adjustment (60-200) • *Push: Reset to 120*
- **Button S1**: Manual step trigger
- **Button S2**: Toggle mutation engine
- **Button S3**: Reset sequence  
- **Button S4**: Toggle idle mode

### Zynthian-Specific Setup
The Zynthian playbook automatically:
- ✅ **Enables GPIO interfaces** (SPI, I2C, GPIO)
- ✅ **Configures hardware permissions** (gpio, audio, i2c groups)
- ✅ **Optimizes for low-latency** (real-time scheduling, CPU governor)
- ✅ **Tests hardware integration** (encoder/button detection)
- ✅ **Uses Zynthian MIDI ports** (built-in DIN connectors)
- ✅ **Disables unnecessary services** (bluetooth, cups, etc.)

## Deployment Options

### Files Overview
- `setup-mystery-music.yml` - **Universal playbook** (standard Pi + Zynthian)
- `setup-zynthian.yml` - **Zynthian-specific** quick deployment
- `inventory.example` - Template with Zynthian hardware groups
- `templates/` - Configuration templates for both setups

### Standard Deployment
```bash
ansible-playbook -i inventory setup-mystery-music.yml
```

### Zynthian Hardware Deployment  
```bash
ansible-playbook -i inventory setup-zynthian.yml
```

### Inventory Configuration

**For Standard Pi:**
```ini
[raspberry_pi]
my-pi ansible_host=192.168.1.100 ansible_user=pi
```

**For Zynthian v4:**
```ini
[raspberry_pi]
zynthian-pi ansible_host=192.168.1.101 ansible_user=pi

[zynthian_hardware]
zynthian-pi is_zynthian_hardware=true
```

## What the Playbooks Do

### Universal Setup (setup-mystery-music.yml)
- **Hardware Detection**: Automatically detects Zynthian v4 hardware
- **System Dependencies**: Python, MIDI libraries, GPIO tools
- **Performance Optimization**: CPU governor, real-time limits, memory tuning
- **Hardware Interfaces**: GPIO, I2C, SPI enablement for Zynthian
- **User Permissions**: Audio, GPIO, MIDI access groups
- **Service Configuration**: Systemd service with hardware-specific settings
- **Monitoring**: Health checks and log rotation

### Zynthian-Specific (setup-zynthian.yml)  
- **Hardware Validation**: Tests encoder/button functionality
- **GPIO Configuration**: Zynthian v4 pin mappings and pull-ups
- **MIDI Interface Setup**: Built-in DIN connector configuration
- **Interactive Testing**: Prompts to test physical controls
- **Performance Tuning**: Low-latency audio/MIDI optimization

### Project Installation
Both playbooks:
- Clone/update Mystery Melody Machine repository  
- Create Python virtual environment
- Install dependencies (including RPi.GPIO for Zynthian)
- Configure appropriate config file (standard vs Zynthian)
- Set up systemd service with correct parameters

## Service Management

The service name is now `mystery-melody` for both standard and Zynthian deployments:

```bash
# Check status
sudo systemctl status mystery-melody

# View logs (includes Zynthian hardware logs)
sudo journalctl -u mystery-melody -f

# Restart service  
sudo systemctl restart mystery-melody

# Test Zynthian hardware (if applicable)
cd /opt/MysteryMelodyEngine/rpi-engine
./check-zynthian-hardware.sh
```

## Configuration Files

### Automatic Configuration Selection
- **Standard Pi**: `config.production.yaml`
- **Zynthian Hardware**: `config.zynthian.yaml` (with hardware controls enabled)

### Zynthian Configuration Features
```yaml
zynthian:
  enabled: true
  encoder_sensitivity: 1
  bpm_step: 5
  min_bpm: 60
  max_bpm: 200

midi:
  input_port: "auto"    # Detects Zynthian MIDI
  output_port: "auto"   # Uses built-in DIN
```

## Monitoring & Troubleshooting

### Health Monitoring
- **Automatic checks**: Every 5 minutes via cron
- **Zynthian hardware validation**: GPIO, MIDI, integration tests
- **Log locations**: `/var/log/mystery-melody/`

```bash
# Manual health check
cd /opt/MysteryMelodyEngine/rpi-engine
./health-check.sh

# Zynthian hardware status (if applicable)
./check-zynthian-hardware.sh
```

### Log Files
- `/var/log/mystery-melody/mystery-melody.log` - Main application
- `/var/log/mystery-melody/mystery-melody-error.log` - Errors  
- `/var/log/mystery-melody/health-check.log` - Health monitoring

### Common Issues

**Zynthian hardware not responding:**
```bash
# Check GPIO permissions
groups $USER | grep gpio

# Test hardware manually
cd /opt/MysteryMelodyEngine/rpi-engine
.venv/bin/python debug/test_zynthian_hardware.py
```

**MIDI devices not found:**
```bash
# Check ALSA MIDI
aconnect -l

# Check for Zynthian MIDI
aconnect -l | grep -E "(pisound|audiophonics|hifiberry)"
```

**Service won't start:**
```bash
# Check detailed logs
sudo journalctl -u mystery-melody -n 50 --no-pager

# Check configuration
cd /opt/MysteryMelodyEngine/rpi-engine
.venv/bin/python -c "from src.config import load_config; print('Config OK')"
```

## Deployment Scenarios

### Single Zynthian Device
```bash
ansible-playbook -i inventory setup-zynthian.yml
```

### Multiple Devices (Mixed)
```bash
# Deploy to all devices with automatic hardware detection
ansible-playbook -i inventory setup-mystery-music.yml

# Deploy only to Zynthian hardware
ansible-playbook -i inventory setup-mystery-music.yml --limit zynthian_hardware
```

### Update Existing Installation
```bash
# Update code only
ansible-playbook -i inventory setup-mystery-music.yml --tags project

# Update configuration only  
ansible-playbook -i inventory setup-mystery-music.yml --tags config

# Full re-deployment
ansible-playbook -i inventory setup-mystery-music.yml
```

## Advanced Configuration

### Performance Tuning Variables
```yaml
# In inventory or group_vars/
enable_performance_tweaks: true
disable_unnecessary_services: true
audio_buffer_size: 64
midi_buffer_size: 32
```

### Zynthian Hardware Variables
```yaml
zynthian_encoder_sensitivity: 1
zynthian_bpm_step: 5
zynthian_min_bpm: 60
zynthian_max_bpm: 200
enable_gpio_optimization: true
```

### Security Hardening
The systemd service includes:
- Non-root execution with minimal privileges
- Restricted filesystem access (with GPIO access for Zynthian)
- Memory limits and resource controls
- Real-time scheduling for hardware responsiveness (Zynthian)
