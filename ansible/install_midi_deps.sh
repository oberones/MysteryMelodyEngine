#!/bin/bash
# Install MIDI dependencies for Raspberry Pi
# This script fixes the "libportmidi.so: cannot open shared object file" error

set -e

echo "Installing MIDI dependencies for Raspberry Pi..."
echo "This will fix the 'libportmidi.so: cannot open shared object file' error"
echo

# Update package database
echo "Updating package database..."
sudo apt-get update

# Install system-level MIDI and audio libraries
echo "Installing system libraries..."
sudo apt-get install -y \
    libportmidi-dev \
    portaudio19-dev \
    libasound2-dev \
    alsa-utils \
    libjack-jackd2-dev \
    pkg-config \
    build-essential

# Load ALSA sequencer module
echo "Loading ALSA sequencer module..."
sudo modprobe snd-seq || echo "snd-seq already loaded or not available"

# Add user to audio groups if not already there
USER_NAME=$(whoami)
echo "Checking user permissions for $USER_NAME..."

if ! groups "$USER_NAME" | grep -q audio; then
    echo "Adding $USER_NAME to audio group..."
    sudo usermod -a -G audio "$USER_NAME"
    echo "Please logout and login again for group changes to take effect"
fi

if ! groups "$USER_NAME" | grep -q dialout; then
    echo "Adding $USER_NAME to dialout group..."
    sudo usermod -a -G dialout "$USER_NAME"
fi

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "Virtual environment detected: $VIRTUAL_ENV"
    
    # Reinstall python-rtmidi to link against new libraries
    echo "Reinstalling python-rtmidi with new system libraries..."
    pip uninstall -y python-rtmidi || echo "python-rtmidi not installed"
    pip install python-rtmidi
    
    # Also reinstall mido to be safe
    echo "Reinstalling mido..."
    pip install --upgrade mido
    
else
    echo "WARNING: No virtual environment detected!"
    echo "Please activate your virtual environment and run:"
    echo "  pip uninstall python-rtmidi"
    echo "  pip install python-rtmidi"
fi

echo
echo "Dependencies installed successfully!"
echo
echo "Next steps:"
echo "1. If you saw group permission messages, logout and login again"
echo "2. Test MIDI ports: python quick_rk006_check_alsa.py"
echo "3. Run the engine: python main_alsa.py --config config.yaml"
echo

# Test the installation
echo "Testing MIDI library installation..."
if python3 -c "import mido; print('✓ mido works'); print(f'Backend: {mido.backend}')"; then
    echo "✓ MIDI libraries are working!"
else
    echo "✗ There may still be issues with MIDI libraries"
    echo "Try running: pip install --force-reinstall python-rtmidi"
fi
