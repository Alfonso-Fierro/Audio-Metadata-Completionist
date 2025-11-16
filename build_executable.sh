#!/bin/bash
# Build script for creating standalone Linux executables

set -e

echo "Audio Metadata Completionist - Build Script"
echo "==========================================="
echo ""

# Check if virtual environment is active
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "Error: Virtual environment not activated!"
    echo "Please run: source .venv/bin/activate"
    exit 1
fi

# Check if PyInstaller is installed
if ! command -v pyinstaller &> /dev/null; then
    echo "Installing PyInstaller..."
    pip install pyinstaller
fi

# Build CLI executable
echo ""
echo "Building CLI executable..."
pyinstaller --onefile \
    --name audio-metadata-cli \
    --add-data "src:src" \
    --hidden-import=mutagen \
    --hidden-import=acoustid \
    --hidden-import=typer \
    main.py

echo "✓ CLI executable created: dist/audio-metadata-cli"

# Build GUI executable (requires python3-tk to be installed)
echo ""
echo "Building GUI executable..."
if python3 -c "import tkinter" 2>/dev/null; then
    pyinstaller --onefile \
        --name audio-metadata-gui \
        --add-data "src:src" \
        --hidden-import=mutagen \
        --hidden-import=acoustid \
        --windowed \
        gui.py
    echo "✓ GUI executable created: dist/audio-metadata-gui"
else
    echo "⚠ Skipping GUI build - tkinter not installed"
    echo "  To build GUI executable, run:"
    echo "  sudo apt-get install python3-tk"
    echo "  Then run this script again."
fi

echo ""
echo "Build complete!"
echo "Executables are in the 'dist' directory"
echo ""
echo "To run:"
echo "  ./dist/audio-metadata-cli --help"
echo "  ./dist/audio-metadata-gui"
