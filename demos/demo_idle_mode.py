#!/usr/bin/env python3
"""
Idle Mode Demo Script

This script demonstrates the idle mode functionality by:
1. Setting up a basic engine with idle detection
2. Showing automatic idle transitions
3. Demonstrating state preservation and restoration
        print("🎮 Interactive Demo Mode")
        print("Commands:")
        print("  'i' - Simulate interaction (resets idle timer)")
        print("  't' - Simulate tempo interaction (preserves BPM on idle exit)")
        print("  'd' - Simulate density interaction (restores BPM on idle exit)")
        print("  'f' - Force idle mode")
        print("  'a' - Force active mode")
        print("  's' - Show current state")
        print("  'h' - Show mutation history")
        print("  'q' - Quit demo")
        print()g mutation engine integration with idle mode
5. Providing interactive controls to test the system

Usage:
    python demo_idle_mode.py

Features demonstrated:
- Automatic idle detection after timeout
- State preservation when entering idle mode
- State restoration when exiting idle mode
- Mutation engine integration (mutations only when idle)
- Manual idle mode control
- Real-time status monitoring
"""

import sys
import os
import time
import threading
from typing import Optional

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from config import IdleConfig, MutationConfig
from state import State, get_state, reset_state
from idle import create_idle_manager
from mutation import create_mutation_engine
from action_handler import ActionHandler
from events import SemanticEvent
from logging_utils import configure_logging


class IdleModeDemo:
    """Interactive demo of idle mode functionality."""
    
    def __init__(self):
        # Reset state for clean demo
        reset_state()
        self.state = get_state()
        
        # Create idle manager with short timeout for demo
        self.idle_config = IdleConfig(
            timeout_ms=5000,  # 5 seconds for demo
            ambient_profile="slow_fade",
            fade_in_ms=1000,
            fade_out_ms=500
        )
        self.idle_manager = create_idle_manager(self.idle_config, self.state)
        
        # Create mutation engine
        self.mutation_config = MutationConfig(
            interval_min_s=10,  # 10 second intervals for demo
            interval_max_s=15,
            max_changes_per_cycle=2
        )
        self.mutation_engine = create_mutation_engine(self.mutation_config, self.state)
        
        # Create action handler
        self.action_handler = ActionHandler(self.state)
        
        # Connect components
        self.action_handler.set_idle_manager(self.idle_manager)
        self.mutation_engine.set_idle_manager(self.idle_manager)
        
        # Demo state
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        # Set up initial state
        self._setup_initial_state()
    
    def _setup_initial_state(self):
        """Set up initial engine state for demonstration."""
        initial_params = {
            'bpm': 120.0,
            'density': 0.8,
            'swing': 0.12,
            'scale_index': 0,  # Major scale
            'master_volume': 100,
            'reverb_mix': 30,
            'filter_cutoff': 70,
            'sequence_length': 8,
        }
        
        print("🎛️  Setting up initial state...")
        for param, value in initial_params.items():
            self.state.set(param, value, source='demo_init')
            print(f"   {param}: {value}")
    
    def start(self):
        """Start the demo."""
        print("\n🚀 Starting Idle Mode Demo")
        print("=" * 50)
        
        # Start all components
        self.idle_manager.start()
        self.mutation_engine.start()
        
        # Start monitoring
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        print("✅ All components started")
        print(f"⏰ Idle timeout: {self.idle_config.timeout_ms/1000:.1f} seconds")
        print(f"🔄 Mutation interval: {self.mutation_config.interval_min_s}-{self.mutation_config.interval_max_s} seconds")
        print()
    
    def stop(self):
        """Stop the demo."""
        print("\n🛑 Stopping demo...")
        self.running = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        
        self.idle_manager.stop()
        self.mutation_engine.stop()
        print("✅ Demo stopped")
    
    def _monitor_loop(self):
        """Monitor and display system status."""
        last_idle_state = None
        
        while self.running:
            try:
                # Get current status
                idle_status = self.idle_manager.get_status()
                mutation_stats = self.mutation_engine.get_stats()
                current_state = self.state.get_all()
                
                # Check for idle state changes
                current_idle = idle_status['is_idle']
                if current_idle != last_idle_state:
                    if current_idle:
                        print(f"\n💤 ENTERED IDLE MODE")
                        print(f"   Profile: {idle_status['current_profile']}")
                        print("   State changes:")
                        idle_params = ['density', 'bpm', 'scale_index', 'reverb_mix', 'filter_cutoff', 'master_volume']
                        for param in idle_params:
                            value = current_state.get(param)
                            if value is not None:
                                print(f"     {param}: {value}")
                    else:
                        print(f"\n🔥 EXITED IDLE MODE")
                        print("   Active state restored")
                    
                    last_idle_state = current_idle
                
                # Display periodic status
                time_display = self._format_time_status(idle_status)
                mutation_display = self._format_mutation_status(mutation_stats)
                
                print(f"\r{time_display} | {mutation_display}", end="", flush=True)
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"\n❌ Monitor error: {e}")
                time.sleep(1.0)
    
    def _format_time_status(self, idle_status):
        """Format idle timing status."""
        if idle_status['is_idle']:
            return "💤 IDLE"
        else:
            time_to_idle = idle_status['time_to_idle']
            return f"⏰ Idle in: {time_to_idle:.1f}s"
    
    def _format_mutation_status(self, mutation_stats):
        """Format mutation status."""
        enabled = "🔄" if mutation_stats['mutations_enabled'] else "⏸️ "
        time_to_next = mutation_stats['time_to_next_mutation_s']
        total = mutation_stats['total_mutations']
        return f"{enabled} Mutations: {total} total, next in {time_to_next:.1f}s"
    
    def simulate_interaction(self, action_type: str = "tempo", value: int = 64):
        """Simulate a MIDI interaction."""
        print(f"\n🎹 Simulating {action_type} interaction (value={value})")
        if action_type == "tempo":
            print("   💡 Note: Tempo interactions preserve BPM when exiting idle mode")
        event = SemanticEvent(type=action_type, source='demo', value=value, raw_note=None)
        self.action_handler.handle_semantic_event(event)
    
    def force_idle(self):
        """Force idle mode for testing."""
        print("\n🔧 Forcing idle mode...")
        self.idle_manager.force_idle()
    
    def force_active(self):
        """Force active mode for testing."""
        print("\n🔧 Forcing active mode...")
        self.idle_manager.force_active()
    
    def show_current_state(self):
        """Display current system state."""
        print(f"\n📊 Current System State")
        print("-" * 30)
        
        # Current parameters
        key_params = ['bpm', 'density', 'swing', 'scale_index', 'master_volume', 'reverb_mix']
        for param in key_params:
            value = self.state.get(param)
            print(f"   {param:15}: {value}")
        
        # Idle status
        idle_status = self.idle_manager.get_status()
        print(f"\n💤 Idle Status:")
        print(f"   Is idle: {idle_status['is_idle']}")
        print(f"   Time since interaction: {idle_status['time_since_last_interaction']:.1f}s")
        print(f"   Time to idle: {idle_status['time_to_idle']:.1f}s")
        
        # Mutation status
        mutation_stats = self.mutation_engine.get_stats()
        print(f"\n🔄 Mutation Status:")
        print(f"   Enabled: {mutation_stats['mutations_enabled']}")
        print(f"   Total mutations: {mutation_stats['total_mutations']}")
        print(f"   Time to next: {mutation_stats['time_to_next_mutation_s']:.1f}s")
    
    def show_mutation_history(self):
        """Display recent mutation history."""
        history = self.mutation_engine.get_history(10)  # Last 10 mutations
        
        print(f"\n📈 Mutation History (last {len(history)} mutations)")
        print("-" * 50)
        
        if not history:
            print("   No mutations recorded yet")
            return
        
        for i, event in enumerate(history, 1):
            time_ago = time.time() - event.timestamp
            print(f"   {i:2d}. {event.parameter:12}: {event.old_value:6.2f} → {event.new_value:6.2f} "
                  f"(Δ{event.delta:+6.2f}) - {time_ago:.0f}s ago")
    
    def run_interactive_demo(self):
        """Run an interactive demo with user commands."""
        print("\n🎮 Interactive Demo Mode")
        print("Commands:")
        print("  'i' - Simulate interaction (resets idle timer)")
        print("  'f' - Force idle mode")
        print("  'a' - Force active mode")
        print("  's' - Show current state")
        print("  'h' - Show mutation history")
        print("  'q' - Quit demo")
        print()
        
        while self.running:
            try:
                cmd = input("\nCommand (i/t/d/f/a/s/h/q): ").strip().lower()
                
                if cmd == 'q':
                    break
                elif cmd == 'i':
                    self.simulate_interaction()
                elif cmd == 't':
                    self.simulate_interaction("tempo", 100)
                elif cmd == 'd':
                    self.simulate_interaction("density", 90)
                elif cmd == 'f':
                    self.force_idle()
                elif cmd == 'a':
                    self.force_active()
                elif cmd == 's':
                    self.show_current_state()
                elif cmd == 'h':
                    self.show_mutation_history()
                else:
                    print("❓ Unknown command")
                    
            except (EOFError, KeyboardInterrupt):
                break


def run_automatic_demo():
    """Run an automatic demo showing idle transitions."""
    print("🎬 Running Automatic Idle Mode Demo")
    print("This demo will show automatic idle detection and recovery")
    
    demo = IdleModeDemo()
    demo.start()
    
    try:
        # Phase 1: Show initial state
        print(f"\n📍 Phase 1: Initial State (5 second idle timeout)")
        demo.show_current_state()
        
        # Phase 2: Wait for automatic idle
        print(f"\n📍 Phase 2: Waiting for automatic idle mode...")
        print("(Watch the timer count down)")
        time.sleep(6)  # Wait longer than timeout
        
        print(f"\n📍 Phase 3: Now in idle mode")
        demo.show_current_state()
        
        # Phase 4: Simulate interaction to exit idle
        print(f"\n📍 Phase 4: Simulating interaction to exit idle mode...")
        demo.simulate_interaction("density", 90)
        time.sleep(1)
        demo.show_current_state()
        
        # Phase 5: Show mutation history
        print(f"\n📍 Phase 5: Mutation History")
        demo.show_mutation_history()
        
        print(f"\n✅ Automatic demo complete!")
        
    except KeyboardInterrupt:
        print(f"\n⏹️  Demo interrupted")
    finally:
        demo.stop()


def run_interactive_demo():
    """Run an interactive demo with user control."""
    demo = IdleModeDemo()
    demo.start()
    
    try:
        demo.run_interactive_demo()
    except KeyboardInterrupt:
        print(f"\n⏹️  Demo interrupted")
    finally:
        demo.stop()


def main():
    """Main demo function."""
    configure_logging("INFO")
    
    print("🎵 Idle Mode Demonstration")
    print("=" * 40)
    print()
    print("This demo showcases Phase 6: Idle Mode functionality")
    print("Features:")
    print("• Automatic idle detection after timeout")
    print("• State preservation and restoration")
    print("• Mutation engine integration (mutations only when idle)")
    print("• Real-time status monitoring")
    print()
    
    # Choose demo mode
    while True:
        choice = input("Choose demo mode:\n  1. Automatic demo\n  2. Interactive demo\n  3. Quit\nChoice (1/2/3): ").strip()
        
        if choice == '1':
            run_automatic_demo()
            break
        elif choice == '2':
            run_interactive_demo()
            break
        elif choice == '3':
            print("👋 Goodbye!")
            break
        else:
            print("❓ Please choose 1, 2, or 3")


if __name__ == "__main__":
    main()
