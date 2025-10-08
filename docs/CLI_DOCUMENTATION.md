# Mystery Music Engine CLI Client

A powerful command-line interface for controlling and monitoring the Mystery Music Engine through its Dynamic Configuration API.

## Installation and Setup

The CLI client is included with the Mystery Music Engine and requires no additional installation.

### Prerequisites
- Mystery Music Engine with API enabled
- Python virtual environment activated (handled automatically by wrapper script)

### Files
- `mme-cli.py` - Main CLI script
- `mme-cli` - Bash wrapper script for easy system access
- `mme-cli-completion.bash` - Bash auto-completion support

## Quick Start

```bash
# Show system status
./mme-cli status

# Get current BPM
./mme-cli config get sequencer.bpm

# Set BPM to 120
./mme-cli config set sequencer.bpm 120

# Quick BPM change
./mme-cli quick bpm 140

# Monitor system in real-time
./mme-cli monitor

# Trigger direction pattern change
./mme-cli event trigger set_direction_pattern ping_pong
```

## Commands Reference

### System Status

#### `status`
Show comprehensive system status including uptime and version information.

```bash
./mme-cli status
```

**Output:**
```
Mystery Music Engine Status
==============================
Status: running
Uptime: 1234.5 seconds
Config Version: 0.1.0
API Version: 1.0.0
```

### Configuration Management

#### `config get [path]`
Get configuration values. Omit path to get complete configuration.

```bash
# Get specific value
./mme-cli config get sequencer.bpm

# Get complete configuration
./mme-cli config get

# Get nested configuration section
./mme-cli config get midi.cc_profile
```

#### `config set <path> <value> [--no-apply]`
Set configuration values. Values are parsed as JSON.

```bash
# Set number
./mme-cli config set sequencer.bpm 120

# Set boolean
./mme-cli config set api.enabled true

# Set string
./mme-cli config set midi.input_port "RK006 IN"

# Set complex value
./mme-cli config set hid.button_mapping '{"0": "trigger_step", "1": "trigger_step"}'

# Don't apply to running system immediately
./mme-cli config set sequencer.bpm 120 --no-apply
```

#### `config list`
List all available configuration paths with types and descriptions.

```bash
./mme-cli config list
```

**Output:**
```
Available Configuration Paths:
=====================================

SEQUENCER:
  sequencer.bpm                (number) - Beats per minute
  sequencer.density            (number) - Note density probability
  sequencer.swing              (number) - Swing timing factor
  ...

MIDI:
  midi.input_port              (string) - MIDI input port name
  midi.output_port             (string) - MIDI output port name
  ...
```

### System State Management

#### `state show [key]`
Show current system state. Optionally specify a specific key.

```bash
# Show all state
./mme-cli state show

# Show specific state key
./mme-cli state show bpm
```

#### `state reset [--confirm]`
Reset system state to defaults.

```bash
# Interactive confirmation
./mme-cli state reset

# Skip confirmation
./mme-cli state reset --confirm
```

### Event Management

#### `event trigger <action> [value]`
Trigger semantic events in the system.

```bash
# Change direction pattern
./mme-cli event trigger set_direction_pattern ping_pong

# Change step pattern
./mme-cli event trigger set_step_pattern syncopated

# Reload CC profile
./mme-cli event trigger reload_cc_profile
```

**Available Events:**
- `set_direction_pattern` - Change sequencer direction (forward, backward, ping_pong, random, fugue, song)
- `set_step_pattern` - Change step pattern (all_on, four_on_the_floor, syncopated)
- `reload_cc_profile` - Reload CC profile configuration

### Real-time Monitoring

#### `monitor [--interval SECONDS]`
Monitor system in real-time with live updates.

```bash
# Default 1-second updates
./mme-cli monitor

# Custom update interval
./mme-cli monitor --interval 0.5
```

**Output:**
```
Status: running | Uptime: 1234.5s
--------------------------------------------------
bpm             : 120.0
density         : 0.86
swing           : 0.09
sequence_length : 4
root_note       : 50

Last update: 14:30:45
```

Press `Ctrl+C` to stop monitoring.

### Quick Commands

#### `quick <param> <value>`
Quick shortcuts for common parameter changes.

```bash
./mme-cli quick bpm 140        # Set BPM
./mme-cli quick density 0.75   # Set density
./mme-cli quick swing 0.15     # Set swing
./mme-cli quick steps 8        # Set sequence length
./mme-cli quick gate 0.8       # Set gate length
./mme-cli quick root 60        # Set root note (C4)
```

**Available Quick Parameters:**
- `bpm` - Beats per minute
- `density` - Note density (0.0-1.0)
- `swing` - Swing amount (0.0-1.0)
- `steps` - Sequence length (steps)
- `gate` - Gate length (0.1-1.0)
- `root` - Root note (MIDI number 0-127)

## Global Options

### Connection Settings

```bash
# Custom API server URL
./mme-cli --url http://192.168.1.100:8080 status

# Custom timeout
./mme-cli --timeout 10.0 status

# Both options
./mme-cli -u http://localhost:9090 -t 2.0 config get sequencer.bpm
```

### Environment Variables

Set default connection parameters:

```bash
export MME_API_URL="http://192.168.1.100:8080"
export MME_API_TIMEOUT="10.0"
```

## Auto-completion

Enable bash auto-completion for faster command entry:

```bash
# One-time enable
source mme-cli-completion.bash

# Add to ~/.bashrc for permanent enable
echo "source $(pwd)/mme-cli-completion.bash" >> ~/.bashrc
```

**Auto-completion Features:**
- Command completion (`status`, `config`, `state`, etc.)
- Subcommand completion (`config get`, `state show`, etc.)
- Configuration path completion
- Event action completion
- Parameter value suggestions

## Error Handling

The CLI provides helpful error messages for common issues:

### Connection Errors
```bash
$ ./mme-cli status
Error: Could not connect to Mystery Music Engine at http://localhost:8080
Make sure the engine is running with API enabled.
```

### Invalid Paths
```bash
$ ./mme-cli config get invalid.path
Configuration path 'invalid.path' not found
```

### Validation Errors
```bash
$ ./mme-cli config set sequencer.bpm "invalid"
Error: Validation error: Input should be a valid number
```

### Timeout Errors
```bash
$ ./mme-cli --timeout 1.0 status
Error: Request timed out after 1.0s
```

## Integration Examples

### Scripts and Automation

```bash
#!/bin/bash
# Performance script - gradually increase tempo

START_BPM=100
END_BPM=140
STEPS=10

for i in $(seq 0 $STEPS); do
    BPM=$(echo "$START_BPM + ($END_BPM - $START_BPM) * $i / $STEPS" | bc -l)
    ./mme-cli quick bpm $BPM
    echo "Set BPM to $BPM"
    sleep 5
done
```

### Live Performance Macros

```bash
#!/bin/bash
# Chaos mode - random settings

./mme-cli event trigger set_direction_pattern random
./mme-cli quick density $(echo "scale=2; $RANDOM / 32767 * 0.5 + 0.5" | bc)
./mme-cli quick swing $(echo "scale=2; $RANDOM / 32767 * 0.3" | bc)
echo "Chaos mode activated!"
```

### System Health Check

```bash
#!/bin/bash
# Health check script

if ./mme-cli status > /dev/null 2>&1; then
    echo "✓ MME API is responsive"
    UPTIME=$(./mme-cli status | grep "Uptime" | cut -d: -f2 | xargs)
    echo "  Uptime: $UPTIME"
else
    echo "✗ MME API is not responding"
    exit 1
fi
```

## Tips and Best Practices

### 1. Use Quick Commands for Live Performance
```bash
# Much faster than full config commands
./mme-cli quick bpm 140
# vs
./mme-cli config set sequencer.bpm 140
```

### 2. Monitor During Development
```bash
# Keep monitoring running in a separate terminal
./mme-cli monitor --interval 0.5
```

### 3. Create Aliases for Common Commands
```bash
# Add to ~/.bashrc
alias mme-status='./mme-cli status'
alias mme-bpm='./mme-cli quick bpm'
alias mme-density='./mme-cli quick density'
```

### 4. Use JSON for Complex Values
```bash
# Set complex button mapping
./mme-cli config set hid.button_mapping '{
  "0": "trigger_step",
  "1": "trigger_step", 
  "2": "tempo"
}'
```

### 5. Combine with Other Tools
```bash
# Use with watch for continuous monitoring
watch -n 1 './mme-cli state show bpm'

# Pipe output for processing
./mme-cli config get sequencer | jq '.bpm'
```

## Troubleshooting

### CLI Won't Start
1. Check virtual environment: `ls .venv/`
2. Ensure dependencies installed: `pip install -r requirements.txt`
3. Use wrapper script: `./mme-cli` instead of `./mme-cli.py`

### Connection Issues
1. Verify engine is running: `ps aux | grep main.py`
2. Check API is enabled in `config.yaml`
3. Test with curl: `curl http://localhost:8080/status`
4. Try different URL: `./mme-cli -u http://127.0.0.1:8080 status`

### Permission Errors
1. Make scripts executable: `chmod +x mme-cli mme-cli.py`
2. Check file ownership: `ls -la mme-cli*`

### Auto-completion Not Working
1. Source completion script: `source mme-cli-completion.bash`
2. Check bash version: `bash --version` (requires bash 4.0+)
3. Reload bash configuration: `source ~/.bashrc`

## Advanced Usage

### Custom API Endpoints
The CLI can be extended to support custom API endpoints by modifying the `MMEClient` class in `mme-cli.py`.

### Configuration Validation
All configuration changes are validated by the server before application, ensuring system stability.

### Batch Operations
```bash
# Multiple quick changes
./mme-cli quick bpm 120 && ./mme-cli quick density 0.8 && ./mme-cli quick swing 0.1
```

### Remote Control
```bash
# Control remote MME instance
./mme-cli -u http://studio-pi.local:8080 quick bpm 140
```
