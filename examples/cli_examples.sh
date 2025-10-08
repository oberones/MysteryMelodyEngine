#!/bin/bash
#
# Mystery Music Engine CLI Examples
# 
# This script demonstrates various CLI usage patterns and can serve as a
# reference for automation and live performance control.

set -e  # Exit on error

CLI="./mme-cli"
echo "Mystery Music Engine CLI Examples"
echo "=================================="

# Check if server is running
echo "1. Checking server status..."
if ! $CLI status > /dev/null 2>&1; then
    echo "❌ MME server is not running or API is not enabled"
    echo "   Please start the engine with: python src/main.py --config config.yaml"
    exit 1
fi

echo "✅ MME server is running"
echo

# Show current status
echo "2. Current system status:"
$CLI status
echo

# Get current configuration
echo "3. Current key parameters:"
echo "   BPM: $($CLI config get sequencer.bpm | cut -d: -f2 | xargs)"
echo "   Density: $($CLI config get sequencer.density | cut -d: -f2 | xargs)"
echo "   Swing: $($CLI config get sequencer.swing | cut -d: -f2 | xargs)"
echo "   Steps: $($CLI config get sequencer.steps | cut -d: -f2 | xargs)"
echo

# Demonstrate quick commands
echo "4. Demonstrating quick parameter changes..."
echo "   Setting BPM to 120..."
$CLI quick bpm 120
echo "   ✅ BPM updated"

echo "   Setting density to 0.8..."
$CLI quick density 0.8
echo "   ✅ Density updated"

echo "   Setting swing to 0.15..."
$CLI quick swing 0.15
echo "   ✅ Swing updated"
echo

# Show state after changes
echo "5. System state after changes:"
$CLI state show | head -10
echo

# Demonstrate event triggering
echo "6. Triggering pattern changes..."
echo "   Changing direction pattern to ping_pong..."
$CLI event trigger set_direction_pattern ping_pong
echo "   ✅ Direction pattern changed"

echo "   Changing step pattern to syncopated..."
$CLI event trigger set_step_pattern syncopated
echo "   ✅ Step pattern changed"
echo

# Demonstrate configuration management
echo "7. Configuration management examples..."
echo "   Current MIDI output port:"
$CLI config get midi.output_port

echo "   Available configuration paths (first 10):"
$CLI config list | head -15
echo

# Automation example
echo "8. Automation example - BPM ramp..."
echo "   Gradually increasing BPM from 110 to 130 over 5 steps..."

START_BPM=110
END_BPM=130
STEPS=5

for i in $(seq 0 $STEPS); do
    # Calculate BPM for this step
    BPM=$(echo "scale=1; $START_BPM + ($END_BPM - $START_BPM) * $i / $STEPS" | bc -l)
    
    echo "   Setting BPM to $BPM..."
    $CLI quick bpm $BPM
    
    # Short delay to hear the change
    sleep 1
done

echo "   ✅ BPM ramp completed"
echo

# Performance macro example
echo "9. Performance macro - 'Chaos Mode'..."
echo "   Applying random settings for dramatic effect..."

# Random density between 0.5 and 1.0
RANDOM_DENSITY=$(echo "scale=2; $RANDOM / 32767 * 0.5 + 0.5" | bc -l)
$CLI quick density $RANDOM_DENSITY
echo "   Random density: $RANDOM_DENSITY"

# Random swing between 0.0 and 0.3
RANDOM_SWING=$(echo "scale=2; $RANDOM / 32767 * 0.3" | bc -l)
$CLI quick swing $RANDOM_SWING
echo "   Random swing: $RANDOM_SWING"

# Random direction pattern
PATTERNS=("forward" "backward" "ping_pong" "random")
RANDOM_PATTERN=${PATTERNS[$RANDOM % ${#PATTERNS[@]}]}
$CLI event trigger set_direction_pattern $RANDOM_PATTERN
echo "   Random direction: $RANDOM_PATTERN"

echo "   ✅ Chaos mode activated!"
echo

# Reset to sensible defaults
echo "10. Resetting to sensible defaults..."
$CLI quick bpm 120
$CLI quick density 0.85
$CLI quick swing 0.12
$CLI event trigger set_direction_pattern forward
echo "    ✅ Reset complete"
echo

echo "🎵 CLI Examples completed successfully!"
echo
echo "Pro Tips:"
echo "- Use '$CLI monitor' for real-time monitoring"
echo "- Create aliases: alias mme-bpm='$CLI quick bpm'"
echo "- Enable auto-completion: source mme-cli-completion.bash"
echo "- Use in scripts for automation and live performance control"
