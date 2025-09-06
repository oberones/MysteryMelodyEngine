"""Integration example for the NTS-1 mutation plugin.

This example shows how to integrate the NTS-1 mutation plugin into
the main Mystery Music Station application.
"""

import logging
from typing import Optional

# Import the plugin
from nts1_mutation_plugin import setup_nts1_mutations, register_nts1_rules

log = logging.getLogger(__name__)


def integrate_nts1_plugin(mutation_engine, state, config_data: dict) -> bool:
    """Integrate NTS-1 mutation plugin based on configuration.
    
    Args:
        mutation_engine: The main mutation engine
        state: The main state system
        config_data: Configuration dictionary
        
    Returns:
        True if plugin was successfully integrated
    """
    try:
        # Check if NTS-1 plugin is enabled in config
        nts1_config = config_data.get("mutation", {}).get("nts1_plugin", {})
        
        if not nts1_config.get("enabled", False):
            log.info("NTS-1 mutation plugin disabled in config")
            return False
        
        # Get plugin style
        style = nts1_config.get("style", "default")
        if style not in ["default", "ambient", "rhythmic"]:
            log.warning(f"Invalid NTS-1 plugin style '{style}', using 'default'")
            style = "default"
        
        # Check if we should replace default rules
        replace_default = nts1_config.get("replace_default_rules", False)
        if replace_default:
            # Clear existing rules
            mutation_engine._rules.clear()
            log.info("Cleared default mutation rules for NTS-1 plugin")
        
        # Set up NTS-1 mutations
        setup_nts1_mutations(mutation_engine, state, style)
        
        log.info(f"NTS-1 mutation plugin integrated successfully (style={style}, replace_default={replace_default})")
        return True
        
    except Exception as e:
        log.error(f"Failed to integrate NTS-1 mutation plugin: {e}")
        return False


def setup_nts1_idle_mode(idle_manager, state, config_data: dict) -> None:
    """Set up NTS-1-specific idle mode behaviors.
    
    Args:
        idle_manager: The idle mode manager
        state: The state system
        config_data: Configuration dictionary
    """
    try:
        nts1_idle_config = config_data.get("idle", {}).get("nts1_idle", {})
        
        if not nts1_idle_config:
            log.debug("No NTS-1 idle configuration found")
            return
        
        def on_idle_enter():
            """Called when entering idle mode - apply NTS-1 ambient settings."""
            log.info("Applying NTS-1 idle mode settings")
            
            # Boost reverb for ambient character
            reverb_boost = nts1_idle_config.get("reverb_boost", 0)
            if reverb_boost > 0:
                current_reverb = state.get("reverb_mix", 32)
                new_reverb = min(127, current_reverb + reverb_boost)
                state.set("reverb_mix", new_reverb, source="nts1_idle")
                log.debug(f"Boosted reverb: {current_reverb} -> {new_reverb}")
            
            # Open filter slightly
            filter_open = nts1_idle_config.get("filter_open", 0)
            if filter_open > 0:
                current_cutoff = state.get("filter_cutoff", 96)
                new_cutoff = min(127, current_cutoff + filter_open)
                state.set("filter_cutoff", new_cutoff, source="nts1_idle")
                log.debug(f"Opened filter: {current_cutoff} -> {new_cutoff}")
            
            # Soften attacks
            slower_attack = nts1_idle_config.get("slower_attack", 0)
            if slower_attack > 0:
                current_attack = state.get("eg_attack", 16)
                new_attack = min(127, current_attack + slower_attack)
                state.set("eg_attack", new_attack, source="nts1_idle")
                log.debug(f"Softened attack: {current_attack} -> {new_attack}")
        
        def on_idle_exit():
            """Called when exiting idle mode - could restore settings."""
            log.info("Exiting NTS-1 idle mode")
            # Could implement restoration of previous values here
            # For now, let mutations handle the evolution back
        
        # Register callbacks with idle manager
        idle_manager.add_idle_enter_callback(on_idle_enter)
        idle_manager.add_idle_exit_callback(on_idle_exit)
        
        log.info("NTS-1 idle mode integration complete")
        
    except Exception as e:
        log.error(f"Failed to set up NTS-1 idle mode: {e}")


def validate_nts1_cc_profile(config_data: dict) -> bool:
    """Validate that the active CC profile is compatible with NTS-1.
    
    Args:
        config_data: Configuration dictionary
        
    Returns:
        True if CC profile is NTS-1 compatible
    """
    try:
        active_profile = config_data.get("midi", {}).get("cc_profile", {}).get("active_profile")
        
        if active_profile == "korg_nts1_mk2":
            log.info("Using official NTS-1 mkII CC profile")
            return True
        elif active_profile and "nts1" in active_profile.lower():
            log.warning(f"Using custom NTS-1 profile: {active_profile}")
            return True
        else:
            log.warning(f"Active CC profile '{active_profile}' may not be optimal for NTS-1")
            log.warning("Consider using 'korg_nts1_mk2' for best results")
            return False
            
    except Exception as e:
        log.error(f"Failed to validate CC profile: {e}")
        return False


# Example usage in main.py
def example_main_integration():
    """Example of how to integrate into main.py"""
    
    # This would be in your main.py file:
    """
    from nts1_integration import integrate_nts1_plugin, setup_nts1_idle_mode, validate_nts1_cc_profile
    
    def main():
        # ... existing setup code ...
        
        # Load configuration
        config_data = load_config("config.yaml")
        
        # Validate CC profile for NTS-1
        validate_nts1_cc_profile(config_data)
        
        # Create state and mutation engine
        state = create_state(config_data)
        mutation_config = config_data.get("mutation", {})
        mutation_engine = create_mutation_engine(mutation_config, state)
        
        # Integrate NTS-1 plugin
        if integrate_nts1_plugin(mutation_engine, state, config_data):
            log.info("NTS-1 plugin integration successful")
        
        # Set up idle manager
        idle_manager = create_idle_manager(config_data, state)
        
        # Set up NTS-1 idle mode
        setup_nts1_idle_mode(idle_manager, state, config_data)
        
        # ... rest of main loop ...
    """
    pass


if __name__ == "__main__":
    # This file is meant to be imported, but we can show the integration pattern
    print("NTS-1 Integration Example")
    print("This file should be imported into your main application")
    print("See example_main_integration() for usage pattern")
