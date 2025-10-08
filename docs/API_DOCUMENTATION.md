# Dynamic Configuration API

The Mystery Music Engine includes a REST API that allows you to modify configuration values while the application is running. This enables real-time parameter changes without requiring a restart.

## Overview

- **Base URL**: `http://localhost:8080` (configurable in `config.yaml`)
- **Format**: JSON REST API
- **Authentication**: None (local access only by default)
- **Documentation**: Available at `/docs` (Swagger UI)

## Configuration

Enable/disable the API in `config.yaml`:

```yaml
api:
  enabled: true
  port: 8080
  host: "0.0.0.0"  # Set to "127.0.0.1" for localhost-only access
  log_level: "info"
```

## API Endpoints

### System Information

#### `GET /`
Basic API information and status.

#### `GET /status`
System status including uptime.

**Response:**
```json
{
  "status": "running",
  "uptime_seconds": 1234.5,
  "config_version": "0.1.0",
  "api_version": "1.0.0"
}
```

### Configuration Management

#### `GET /config`
Get the complete current configuration.

#### `GET /config/{path}`
Get a specific configuration value by dot-separated path.

**Example:** `GET /config/sequencer.bpm`

**Response:**
```json
{
  "path": "sequencer.bpm",
  "value": 85.0,
  "exists": true
}
```

#### `POST /config`
Update a configuration value.

**Request Body:**
```json
{
  "path": "sequencer.bpm",
  "value": 95.0,
  "apply_immediately": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Configuration updated successfully: sequencer.bpm and applied to running system",
  "old_value": 85.0,
  "new_value": 95.0,
  "applied_to_state": true
}
```

### System State

#### `GET /state`
Get the current internal system state.

#### `POST /state/reset`
Reset the system state to defaults.

### Schema and Metadata

#### `GET /config/schema`
Get the complete configuration schema for validation.

#### `GET /config/mappings`
Get information about all supported configuration paths and their types.

### Semantic Events

#### `POST /actions/semantic`
Trigger semantic events in the system.

**Parameters:**
- `action`: Event action name
- `value`: Optional event value
- `source`: Source identifier (defaults to "api")

**Example:** `POST /actions/semantic?action=set_direction_pattern&value=ping_pong`

## Configuration Paths

Here are the main configuration paths you can modify:

### Sequencer Parameters
- `sequencer.bpm` - Beats per minute (float)
- `sequencer.swing` - Swing amount 0.0-1.0 (float)
- `sequencer.density` - Note density 0.0-1.0 (float)
- `sequencer.steps` - Number of steps (int)
- `sequencer.root_note` - Root note MIDI number (int, 0-127)
- `sequencer.gate_length` - Note duration fraction (float, 0.1-1.0)
- `sequencer.voices` - Number of voices for fugue mode (int, 1-4)
- `sequencer.direction_pattern` - Pattern direction ("forward", "backward", "ping_pong", "random", "fugue", "song")
- `sequencer.step_pattern` - Step pattern preset name

### MIDI Configuration
- `midi.input_port` - MIDI input port name (string)
- `midi.output_port` - MIDI output port name (string)
- `midi.input_channel` - MIDI input channel (int, 1-16)
- `midi.output_channel` - MIDI output channel (int, 1-16)
- `midi.clock.enabled` - Enable MIDI clock output (bool)
- `midi.cc_profile.active_profile` - Active CC profile name (string)
- `midi.cc_profile.parameter_smoothing` - Enable parameter smoothing (bool)
- `midi.cc_profile.cc_throttle_ms` - CC throttle time in ms (int)

### Mutation Engine
- `mutation.interval_min_s` - Minimum mutation interval in seconds (int)
- `mutation.interval_max_s` - Maximum mutation interval in seconds (int)
- `mutation.max_changes_per_cycle` - Max changes per mutation cycle (int)

### Idle Management
- `idle.timeout_ms` - Idle timeout in milliseconds (int)
- `idle.ambient_profile` - Ambient profile name (string)
- `idle.fade_in_ms` - Fade in time in milliseconds (int)
- `idle.fade_out_ms` - Fade out time in milliseconds (int)
- `idle.smooth_bpm_transitions` - Enable smooth BPM transitions (bool)
- `idle.bpm_transition_duration_s` - BPM transition duration in seconds (float)

### HID Input
- `hid.device_name` - HID device name (string)
- `hid.button_mapping` - Button mapping dictionary
- `hid.joystick_mapping` - Joystick mapping dictionary

### Logging
- `logging.level` - Log level ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

## Examples

### Using curl

```bash
# Get current BPM
curl http://localhost:8080/config/sequencer.bpm

# Set BPM to 120
curl -X POST http://localhost:8080/config \
  -H "Content-Type: application/json" \
  -d '{"path": "sequencer.bpm", "value": 120.0}'

# Change direction pattern
curl -X POST "http://localhost:8080/actions/semantic?action=set_direction_pattern&value=ping_pong"

# Get system status
curl http://localhost:8080/status
```

### Using Python

See `examples/api_demo.py` for a complete Python client example:

```bash
cd rpi-engine
python examples/api_demo.py

# Or run interactively
python examples/api_demo.py --interactive
```

### Using the API Client

```python
from examples.api_demo import APIClient

client = APIClient("http://localhost:8080")

# Get status
status = client.get_status()
print(f"Uptime: {status['uptime_seconds']}s")

# Update configuration
result = client.update_config("sequencer.bpm", 130.0)
print(result['message'])

# Get current state
state = client.get_state()
print(f"Current BPM: {state['bpm']}")
```

## Integration with External Tools

The API can be integrated with external tools for live performance control:

1. **TouchOSC/OSC Controllers**: Use HTTP bridge to convert OSC to API calls
2. **Max/MSP or Pure Data**: Use HTTP objects to send API requests
3. **Ableton Live**: Use Max for Live devices to control parameters
4. **Web Interface**: Build custom web UIs that communicate with the API
5. **Hardware Controllers**: Use microcontrollers with WiFi to send HTTP requests

## Error Handling

The API returns standard HTTP status codes:

- `200 OK` - Success
- `400 Bad Request` - Validation error or malformed request
- `404 Not Found` - Configuration path not found
- `500 Internal Server Error` - Server error

Error responses include detailed error messages:

```json
{
  "detail": "Validation error: Value must be between 0.0 and 1.0"
}
```

## Security Considerations

- The API runs on all interfaces by default (`0.0.0.0`)
- For production use, consider setting `host: "127.0.0.1"` for localhost-only access
- Use a firewall to restrict access to the API port
- The API does not include authentication - implement a reverse proxy with auth if needed

## Performance Notes

- Configuration updates are applied immediately to the running system
- Changes to timing-critical parameters (BPM, swing) are handled gracefully
- The API server runs in a separate thread and doesn't impact audio performance
- All configuration changes are validated before application

## Troubleshooting

### API Server Won't Start
- Check that the port is not already in use
- Verify `api.enabled: true` in config.yaml
- Check logs for initialization errors

### Configuration Changes Not Applied
- Ensure `apply_immediately: true` in update requests
- Check that the configuration path is valid
- Verify the value type matches the expected schema
- Check system logs for application errors

### Connection Refused
- Verify the engine is running
- Check the API port in config.yaml
- Ensure firewall allows connections to the API port
