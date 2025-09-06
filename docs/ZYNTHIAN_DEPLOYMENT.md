# Deploying Mystery Melody Machine on Zynthian v4 Hardware

This guide explains how to deploy the Mystery Melody Machine on Zynthian v4 hardware without running the full Zynthian OS.

## Hardware Overview

The Zynthian v4 kit provides:
- **Raspberry Pi 4** (2GB/4GB/8GB RAM)
- **4 rotary encoders** with push buttons
- **4 additional push buttons** (S1-S4)
- **3.5" TFT display** (480x320)
- **Built-in MIDI DIN connectors** (IN/OUT/THRU)
- **Audio interface** (Hifiberry, AudioInjector, etc.)
- **Custom GPIO hat** with all controls

## Control Mapping

### Encoders (with push buttons)
- **Encoder 0 (Layer)**: MIDI Input Channel (1-16)
  - *Push*: Reset to channel 1
- **Encoder 1 (Back)**: MIDI Output Channel (1-16)
  - *Push*: Reset to channel 1
- **Encoder 2 (Select)**: CC Profile cycling
  - *Push*: Reset to first profile
- **Encoder 3 (Learn)**: BPM adjustment (60-200)
  - *Push*: Reset to 120 BPM

### Push Buttons
- **S1**: Manual step trigger
- **S2**: Toggle mutation engine on/off
- **S3**: Reset sequence to beginning
- **S4**: Toggle idle mode on/off

## Installation Steps

### 1. Prepare Raspberry Pi

Install a clean Raspberry Pi OS (not Zynthian OS):

```bash
# Flash Raspberry Pi OS Lite to SD card
# Enable SSH, configure WiFi if needed
# Boot and SSH into the Pi
```

### 2. Clone and Setup the Project

```bash
# Clone the repository
git clone https://github.com/oberones/MysteryMelodyEngine.git
cd MysteryMelodyEngine/rpi-engine

# Create virtual environment
make setup

# Install Zynthian-specific dependencies
sudo apt update
sudo apt install -y python3-pip python3-venv git libasound2-dev

# The RPi.GPIO dependency will be automatically installed on Linux
```

### 3. Configure Hardware Access

Enable GPIO and audio interfaces:

```bash
# Add user to audio and gpio groups
sudo usermod -a -G audio,gpio $USER

# Enable interfaces in /boot/config.txt
sudo nano /boot/config.txt

# Add these lines:
dtparam=spi=on
dtparam=i2c=on
gpio=4,0,1,7,25,26,27,21,23,12,2,3=pu
```

### 4. Configure MIDI Hardware

For Zynthian hardware with built-in MIDI:

```bash
# Check available MIDI ports
aconnect -l

# You should see hardware MIDI ports like:
# client 14: 'pisound' [type=kernel]
#     0 'pisound MIDI PS-xxxxxx'
```

### 5. Use Zynthian Configuration

Copy the Zynthian example configuration:

```bash
cp examples/config.zynthian.example.yaml config.yaml

# Edit the configuration as needed
nano config.yaml
```

### 6. Test the Hardware Integration

Run a quick test:

```bash
# Test basic functionality
make run-config CONFIG=config.yaml

# Check logs for Zynthian integration
tail -f logs/mystery-melody.log | grep -i zynthian
```

### 7. Set Up Auto-Start Service

Create a systemd service for automatic startup:

```bash
# Copy the service template
sudo cp ansible/templates/mystery-music.service.j2 /etc/systemd/system/mystery-melody.service

# Edit the service file
sudo nano /etc/systemd/system/mystery-melody.service

# Update paths and user as needed:
[Unit]
Description=Mystery Melody Machine
After=network.target sound.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/MysteryMelodyEngine/rpi-engine
ExecStart=/home/pi/MysteryMelodyEngine/rpi-engine/venv/bin/python src/main.py --config config.yaml
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target

# Enable and start the service
sudo systemctl enable mystery-melody
sudo systemctl start mystery-melody
```

## Configuration Options

### Basic Zynthian Configuration

```yaml
# Enable Zynthian hardware
zynthian:
  enabled: true
  encoder_sensitivity: 1    # Steps per encoder click
  bpm_step: 5              # BPM change per step
  min_bpm: 60              # Minimum BPM
  max_bpm: 200             # Maximum BPM
  display_updates: true    # Future: TFT display

# Use hardware MIDI ports
midi:
  input_port: "auto"       # Auto-detect Zynthian MIDI
  output_port: "auto"      # Auto-detect Zynthian MIDI
  input_channel: 1         # Adjustable via encoder
  output_channel: 1        # Adjustable via encoder
```

### Advanced Configuration

```yaml
# Optimize for hardware performance
midi:
  cc_profile:
    cc_throttle_ms: 5      # Lower latency for hardware controls
  clock:
    enabled: true          # Sync external devices

# Performance-optimized sequencer
sequencer:
  steps: 8                 # Good for hardware control
  bpm: 120                 # Encoder adjustable
  voices: 2                # Polyphonic capability

# Longer mutation intervals for live use
mutation:
  interval_min_s: 45
  interval_max_s: 90
  max_changes_per_cycle: 3

# Live performance idle settings
idle:
  timeout_ms: 60000        # 1 minute timeout
  smooth_bpm_transitions: true
```

## Troubleshooting

### GPIO Permission Issues

```bash
# Add user to gpio group
sudo usermod -a -G gpio $USER

# Reboot to apply group changes
sudo reboot
```

### MIDI Port Detection Issues

```bash
# Check ALSA MIDI ports
aconnect -l

# Check raw MIDI devices
ls -la /dev/midi*

# Test MIDI with amidi
amidi -l
```

### Hardware Detection Issues

```bash
# Check GPIO access
gpio readall

# Test individual pins
echo "Testing encoder pins..."
python3 -c "
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(27, GPIO.IN, pull_up_down=GPIO.PUD_UP)
print(f'Pin 27 state: {GPIO.input(27)}')
GPIO.cleanup()
"
```

### Performance Optimization

```bash
# Disable unnecessary services
sudo systemctl disable bluetooth
sudo systemctl disable wifi-powersave

# Set CPU governor to performance
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Reduce audio latency
echo "@audio - rtprio 95" | sudo tee -a /etc/security/limits.conf
echo "@audio - memlock unlimited" | sudo tee -a /etc/security/limits.conf
```

## Integration with External Synthesizers

The Zynthian hardware's built-in MIDI DIN connectors work perfectly with external synthesizers:

```yaml
# Example for Roland JX-08 via MIDI DIN
midi:
  output_port: "auto"  # Uses Zynthian's MIDI OUT
  cc_profile:
    active_profile: "roland_jx08"

# Example for Korg NTS-1 MK2 via MIDI DIN  
midi:
  output_port: "auto"
  cc_profile:
    active_profile: "korg_nts1_mk2"
```

## Future Enhancements

- **TFT Display Integration**: Show current state, BPM, active profile
- **Audio Integration**: Use Zynthian's audio interface for monitoring
- **Preset Management**: Save/load configurations via hardware buttons
- **MIDI Learn**: Use hardware controls to learn MIDI mappings

## Support

For Zynthian-specific hardware questions:
- [Zynthian Community Forum](https://discourse.zynthian.org/)
- [Zynthian Hardware Documentation](https://wiki.zynthian.org/index.php/Zynthian_Hardware)

For Mystery Melody Machine issues:
- Check logs: `journalctl -u mystery-melody -f`
- GPIO debug mode: Set log level to DEBUG in config.yaml
