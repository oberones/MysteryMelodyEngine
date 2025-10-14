"""
Dynamic Configuration API Server for Mystery Music Engine

Provides RESTful API endpoints to modify configuration values at runtime.
"""

import logging
import threading
import time
from typing import Any, Dict, Optional, List, Union
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError

from config import RootConfig
from state import get_state
from events import SemanticEvent


log = logging.getLogger(__name__)


class ConfigUpdateRequest(BaseModel):
    """Request model for updating configuration values."""
    path: str = Field(..., description="Dot-separated path to the config value (e.g., 'sequencer.bpm')")
    value: Any = Field(..., description="New value to set")
    apply_immediately: bool = Field(True, description="Whether to apply the change immediately to the running system")


class ConfigUpdateResponse(BaseModel):
    """Response model for configuration updates."""
    success: bool
    message: str
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    applied_to_state: bool = False


class ConfigGetResponse(BaseModel):
    """Response model for getting configuration values."""
    path: str
    value: Any
    exists: bool = True


class SystemStatusResponse(BaseModel):
    """Response model for system status."""
    status: str
    uptime_seconds: float
    config_version: str = "0.1.0"
    api_version: str = "1.0.0"


class APIServer:
    """FastAPI server for dynamic configuration management."""
    
    def __init__(self, config: RootConfig, semantic_event_handler=None):
        """Initialize the API server.
        
        Args:
            config: Current configuration object
            semantic_event_handler: Optional handler for semantic events
        """
        self.config = config
        self.semantic_event_handler = semantic_event_handler
        self.start_time = time.time()
        self._server = None
        self._thread = None
        self._running = False
        
        # Create FastAPI app
        self.app = FastAPI(
            title="Mystery Music Engine API",
            description="Dynamic configuration API for the Mystery Music Engine",
            version="1.0.0",
            lifespan=self.lifespan
        )
        
        self._setup_routes()
    
    @asynccontextmanager
    async def lifespan(self, app: FastAPI):
        """Lifespan context manager for FastAPI."""
        log.info("API server starting up")
        yield
        log.info("API server shutting down")
    
    def _setup_routes(self):
        """Set up API routes."""
        
        @self.app.get("/", response_model=Dict[str, str])
        async def root():
            """Root endpoint with basic API information."""
            return {
                "name": "Mystery Music Engine API",
                "version": "1.0.0",
                "status": "running",
                "docs": "/docs"
            }
        
        @self.app.get("/status", response_model=SystemStatusResponse)
        async def get_status():
            """Get system status."""
            return SystemStatusResponse(
                status="running",
                uptime_seconds=time.time() - self.start_time
            )
        
        @self.app.get("/config", response_model=Dict[str, Any])
        async def get_full_config():
            """Get the complete current configuration."""
            return self.config.model_dump()
        
        @self.app.get("/config/schema")
        async def get_config_schema():
            """Get the configuration schema for validation."""
            return RootConfig.model_json_schema()
        
        @self.app.get("/config/mappings")
        async def get_supported_mappings():
            """Get information about supported configuration paths and their types."""
            schema = RootConfig.model_json_schema()
            self._root_schema = schema  # Store for reference resolution
            return self._extract_schema_paths(schema)
        
        @self.app.get("/config/{config_path:path}", response_model=ConfigGetResponse)
        async def get_config_value(config_path: str):
            """Get a specific configuration value by path."""
            try:
                value = self._get_config_value(config_path)
                return ConfigGetResponse(path=config_path, value=value)
            except KeyError:
                return ConfigGetResponse(path=config_path, value=None, exists=False)
        
        @self.app.post("/config", response_model=ConfigUpdateResponse)
        async def update_config(
            request: ConfigUpdateRequest,
            background_tasks: BackgroundTasks
        ):
            """Update a configuration value."""
            try:
                # Get old value
                try:
                    old_value = self._get_config_value(request.path)
                except KeyError:
                    old_value = None
                
                # Update configuration
                self._set_config_value(request.path, request.value)
                
                response = ConfigUpdateResponse(
                    success=True,
                    message=f"Configuration updated successfully: {request.path}",
                    old_value=old_value,
                    new_value=request.value,
                    applied_to_state=False
                )
                
                # Apply to running system if requested
                if request.apply_immediately:
                    background_tasks.add_task(
                        self._apply_config_to_system, 
                        request.path, 
                        request.value
                    )
                    response.applied_to_state = True
                    response.message += " and applied to running system"
                
                return response
                
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=f"Validation error: {e}")
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Value error: {e}")
            except Exception as e:
                log.error(f"Error updating config {request.path}: {e}")
                raise HTTPException(status_code=500, detail=f"Internal error: {e}")
        
        @self.app.get("/state", response_model=Dict[str, Any])
        async def get_system_state():
            """Get the current system state."""
            state = get_state()
            return state.get_all()
        
        @self.app.post("/state/reset")
        async def reset_system_state():
            """Reset the system state to defaults."""
            from state import reset_state
            reset_state()
            return {"message": "System state reset successfully"}
        
        @self.app.post("/actions/semantic")
        async def trigger_semantic_event(
            action: str,
            value: Optional[Any] = None,
            source: str = "api"
        ):
            """Trigger a semantic event in the system."""
            if not self.semantic_event_handler:
                raise HTTPException(status_code=503, detail="Semantic event handler not available")
            
            try:
                event = SemanticEvent(type=action, value=value, source=source)
                self.semantic_event_handler(event)
                return {"message": f"Semantic event '{action}' triggered successfully"}
            except Exception as e:
                log.error(f"Error triggering semantic event: {e}")
                raise HTTPException(status_code=500, detail=f"Error triggering event: {e}")
    
    def _get_config_value(self, path: str) -> Any:
        """Get a configuration value by dot-separated path."""
        keys = path.split('.')
        current = self.config.model_dump()
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                raise KeyError(f"Configuration path not found: {path}")
        
        return current
    
    def _set_config_value(self, path: str, value: Any) -> None:
        """Set a configuration value by dot-separated path."""
        keys = path.split('.')
        
        # Build the update dict
        config_dict = self.config.model_dump()
        current = config_dict
        
        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # Set the final value
        current[keys[-1]] = value
        
        # Validate the entire config by recreating it
        try:
            self.config = RootConfig(**config_dict)
        except ValidationError as e:
            raise ValueError(f"Configuration validation failed: {e}")
    
    def _apply_config_to_system(self, path: str, value: Any) -> None:
        """Apply configuration changes to the running system."""
        try:
            state = get_state()
            
            # Map config paths to state keys where applicable
            path_mappings = {
                'sequencer.bpm': 'bpm',
                'sequencer.swing': 'swing', 
                'sequencer.density': 'density',
                'sequencer.steps': 'sequence_length',
                'sequencer.root_note': 'root_note',
                'sequencer.gate_length': 'gate_length',
                'sequencer.voices': 'voices',
                'idle.smooth_bpm_transitions': 'smooth_idle_transitions',
                'idle.bpm_transition_duration_s': 'idle_transition_duration_s',
            }
            
            if path in path_mappings:
                state_key = path_mappings[path]
                state.set(state_key, value, source='api')
                log.info(f"Applied config change to state: {state_key}={value}")
            
            # Handle special cases that need semantic events
            if path == 'sequencer.direction_pattern' and self.semantic_event_handler:
                event = SemanticEvent(type='set_direction_pattern', value=value, source='api')
                self.semantic_event_handler(event)
                log.info(f"Triggered semantic event for direction pattern: {value}")
            
            elif path == 'sequencer.step_pattern' and self.semantic_event_handler:
                event = SemanticEvent(type='set_step_pattern', value=value, source='api')
                self.semantic_event_handler(event)
                log.info(f"Triggered semantic event for step pattern: {value}")
            
            elif path.startswith('midi.cc_profile') and self.semantic_event_handler:
                event = SemanticEvent(type='reload_cc_profile', value=None, source='api')
                self.semantic_event_handler(event)
                log.info("Triggered CC profile reload")
                
        except Exception as e:
            log.error(f"Error applying config to system: {e}")
            raise
    
    def _extract_schema_paths(self, schema: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Extract all possible configuration paths from the schema."""
        paths = {}
        
        # Helper function to resolve $ref references
        def resolve_ref(ref_schema: Dict[str, Any], root_schema: Dict[str, Any]) -> Dict[str, Any]:
            if "$ref" in ref_schema:
                ref_path = ref_schema["$ref"]
                if ref_path.startswith("#/$defs/"):
                    def_name = ref_path[8:]  # Remove "#/$defs/"
                    return root_schema.get("$defs", {}).get(def_name, {})
            return ref_schema
        
        if "properties" in schema:
            for prop_name, prop_schema in schema["properties"].items():
                current_path = f"{prefix}.{prop_name}" if prefix else prop_name
                
                # Resolve any $ref references
                resolved_schema = resolve_ref(prop_schema, schema if not prefix else self._root_schema)
                
                if resolved_schema.get("type") == "object" and "properties" in resolved_schema:
                    # Recursively handle nested objects
                    nested_paths = self._extract_schema_paths(resolved_schema, current_path)
                    paths.update(nested_paths)
                else:
                    # Leaf property
                    paths[current_path] = {
                        "type": resolved_schema.get("type", "unknown"),
                        "description": resolved_schema.get("description", ""),
                        "default": resolved_schema.get("default"),
                        "enum": resolved_schema.get("enum"),
                        "minimum": resolved_schema.get("minimum"),
                        "maximum": resolved_schema.get("maximum"),
                    }
        
        return paths
    
    def start(self) -> None:
        """Start the API server in a background thread."""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(
            target=self._run_server,
            daemon=True,
            name="api-server"
        )
        self._thread.start()
        log.info(f"API server starting on port {self.config.api.port}")
    
    def stop(self) -> None:
        """Stop the API server."""
        if not self._running:
            return
        
        self._running = False
        if self._server:
            self._server.should_exit = True
        
        if self._thread:
            self._thread.join(timeout=5.0)
        
        log.info("API server stopped")
    
    def _run_server(self) -> None:
        """Run the FastAPI server using uvicorn."""
        try:
            config = uvicorn.Config(
                self.app,
                host=self.config.api.host,
                port=self.config.api.port,
                log_level="info" if log.isEnabledFor(logging.INFO) else "warning",
                access_log=True
            )
            self._server = uvicorn.Server(config)
            self._server.run()
        except Exception as e:
            log.error(f"API server error: {e}")
            self._running = False


def create_api_server(config: RootConfig, semantic_event_handler=None) -> Optional[APIServer]:
    """Create and configure the API server if enabled."""
    if not config.api.enabled:
        log.info("API server disabled in configuration")
        return None
    
    try:
        server = APIServer(config, semantic_event_handler)
        return server
    except Exception as e:
        log.error(f"Failed to create API server: {e}")
        return None
