# Linux Installation & Executable Guide

This guide provides multiple ways to run Audio Metadata Completionist on Linux.

## Quick Start - Launcher Scripts (Recommended)

The easiest way to run the application:

### 1. Install tkinter (required for GUI only)

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-tk
```

**Fedora/RHEL:**
```bash
sudo dnf install python3-tkinter
```

**Arch Linux:**
```bash
sudo pacman -S tk
```

### 2. Run the application

**CLI version:**
```bash
./audio-metadata --help
./audio-metadata /path/to/music/folder
```

**GUI version:**
```bash
./audio-metadata-gui
```

The launcher scripts will automatically activate the virtual environment and run the application.

---

## Building Standalone Executables

If you want to create standalone executables that don't require Python to be installed on the target system:

### Prerequisites

1. Install tkinter (see above)
2. Activate your virtual environment:
   ```bash
   source .venv/bin/activate
   ```

### Build

Run the build script:
```bash
./build_executable.sh
```

This will create two executables in the `dist/` directory:
- `dist/audio-metadata-cli` - Command-line version
- `dist/audio-metadata-gui` - GUI version

### Run the standalone executables

```bash
./dist/audio-metadata-cli --help
./dist/audio-metadata-gui
```

These executables can be copied to `/usr/local/bin/` or `~/.local/bin/` for system-wide access.

---

## Direct Execution (Development)

If you're developing or want to run directly:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run CLI
python main.py --help
# or
./main.py --help

# Run GUI
python gui.py
# or
./gui.py
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'tkinter'"

Install the system tkinter package (see step 1 under Quick Start).

### "ModuleNotFoundError: No module named 'typer'" or other dependencies

Make sure your virtual environment is activated and dependencies are installed:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### "Failed building wheel for pyacoustid"

If you encounter installation errors with `pyacoustid`, try installing system dependencies first:

**Ubuntu/Debian:**
```bash
sudo apt-get install libchromaprint-dev libffi-dev python3-dev
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

**Fedora/RHEL:**
```bash
sudo dnf install chromaprint-devel libffi-devel python3-devel
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

**Arch Linux:**
```bash
sudo pacman -S chromaprint
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Permission denied when running scripts

Make sure the scripts are executable:
```bash
chmod +x audio-metadata audio-metadata-gui build_executable.sh
```

---

## Installing to System PATH

To make the application available system-wide:

**Option 1: Using launcher scripts**
```bash
sudo ln -s $(pwd)/audio-metadata /usr/local/bin/audio-metadata
sudo ln -s $(pwd)/audio-metadata-gui /usr/local/bin/audio-metadata-gui
```

**Option 2: Using standalone executables**
```bash
./build_executable.sh
sudo cp dist/audio-metadata-cli /usr/local/bin/audio-metadata
sudo cp dist/audio-metadata-gui /usr/local/bin/audio-metadata-gui
```

Then you can run from anywhere:
```bash
audio-metadata --help
audio-metadata-gui
```
