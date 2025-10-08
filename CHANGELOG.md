# Changelog

All notable changes to the Mystery Music Engine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Dynamic Configuration API**: REST API for real-time configuration changes
  - FastAPI-based server with automatic OpenAPI documentation
  - Support for updating all configuration parameters at runtime
  - Configuration validation and error handling
  - System state monitoring and control endpoints
  - Semantic event triggering via API
  - Python client example and interactive demo
  - Comprehensive API documentation

### Changed
- Enhanced configuration system to support runtime updates
- Added API configuration section to config.yaml
- Extended action handler to support API-triggered events

### Dependencies
- Added `fastapi` for API server framework
- Added `uvicorn` for ASGI server
- Added `requests` for API client examples

---

## Previous Versions

### [0.7.0] - Phase 7 Implementation
- External hardware integration with CC profiles
- MIDI clock synchronization
- Parameter smoothing and throttling

### [0.6.0] - Phase 6 Implementation  
- Idle mode detection and ambient profiles
- Activity tracking and smooth transitions

### [0.5.5] - Phase 5.5 Implementation
- Enhanced sequencer patterns (step patterns, direction patterns)
- Fugue mode and song mode implementations
- Multi-voice polyphonic sequencing

### [0.5.0] - Phase 5 Implementation
- Advanced pattern generation
- Scale quantization improvements
- Pattern direction controls

### [0.4.0] - Phase 4 Implementation
- External synth support
- MIDI output routing
- Latency optimization

### [0.3.0] - Phase 3 Implementation
- Integration testing
- Performance optimization
- Error handling improvements

### [0.2.0] - Phase 2 Implementation
- Basic sequencer functionality
- MIDI input/output
- State management
- Mutation engine

### [0.1.0] - Initial Release
- Core architecture
- Configuration system
- Basic MIDI handling