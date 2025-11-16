# 🎵 Audio Metadata Completionist

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Professional-grade audio metadata enrichment tool that automatically identifies songs, fetches metadata, and downloads album artwork for your music collection. Perfect for organizing your music library for use with VLC and other media players.

## ✨ Features

- **🎯 Audio Fingerprinting**: Identify songs using acoustic fingerprinting (AcousticID/Chromaprint)
- **📊 Rich Metadata**: Fetch comprehensive metadata from MusicBrainz database
- **🎨 Album Artwork**: Download high-quality album covers from multiple sources
  - Cover Art Archive (official MusicBrainz artwork)
  - iTunes API
  - Extensible architecture for adding more providers
- **📁 Batch Processing**: Process individual files or entire directories recursively
- **🔄 Smart Merging**: Intelligently merge existing metadata with identified data
- **💾 Multiple Formats**: Support for MP3, FLAC, M4A, OGG, WAV, WMA
- **⚡ Concurrent Processing**: Fast parallel processing of multiple files
- **🎯 Type-Safe**: Strict typing throughout with Pydantic models
- **📝 Comprehensive Logging**: Detailed logging for debugging and monitoring
- **💰 Cache System**: Built-in caching to reduce API calls and improve performance
- **🧪 Well-Tested**: Extensive unit and integration test coverage

## 📋 Requirements

- Python 3.10 or higher
- Chromaprint/fpcalc for audio fingerprinting
- FFmpeg for audio decoding
- AcousticID API key (free registration at https://acoustid.org/api-key)

## 🚀 Installation

### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3.10 python3-pip python3-tk libchromaprint-tools ffmpeg
```

**macOS (using Homebrew):**
```bash
brew install python@3.10 chromaprint ffmpeg
```

**Windows:**
1. Download and install Chromaprint from: https://acoustid.org/chromaprint
2. Download and install FFmpeg from: https://ffmpeg.org/download.html

### 2. Clone the Repository

```bash
git clone https://github.com/Alfonso-Fierro/Audio-Metadata-Completionist.git
cd Audio-Metadata-Completionist
```

### 3. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your AcousticID API key:
```bash
ACOUSTID_API_KEY=your_api_key_here
MUSICBRAINZ_CONTACT_EMAIL=your_email@example.com
```

Get your free AcousticID API key from: https://acoustid.org/api-key

## 📖 Usage

### Graphical User Interface (GUI)

For the easiest experience, especially with folders containing Unicode characters or spaces in their names:

```bash
python gui.py
```

The GUI provides:
- **Simple folder selection** - Browse and select any folder, including those with Unicode characters
- **Visual options** - Toggle settings with checkboxes
- **Real-time feedback** - See processing status and results
- **No command-line complexity** - Perfect for users who prefer a visual interface

![GUI Screenshot](docs/gui-screenshot.png)

### Command Line Interface

#### Enrich Audio Files

Process a single file:
```bash
python main.py enrich /path/to/song.mp3
```

Process an entire directory:
```bash
python main.py enrich /path/to/music/folder
```

**Note:** For paths with spaces or Unicode characters, use quotes:
```bash
python main.py enrich "/path/to/ペルソナ3 リロード オリジナル・サウンドトラック - ATLUS Sound Team"
```

Process with options:
```bash
python main.py enrich /path/to/music \
  --recursive \
  --skip-existing \
  --force-artwork \
  --max-concurrent 8
```

#### Options

- `--recursive / -r`: Search directories recursively (default: True)
- `--skip-existing / -s`: Skip files that already have complete metadata
- `--force-artwork / -a`: Force artwork download even if it exists
- `--dry-run / -d`: Preview changes without writing to files
- `--max-concurrent / -c`: Maximum concurrent operations (default: 4)
- `--log-level / -l`: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

#### View File Information

```bash
python main.py info /path/to/song.mp3
```

#### Clear Cache

```bash
python main.py clear-cache
```

### Python API

```python
import asyncio
from pathlib import Path
from src.core.audio_file import AudioFile
from src.pipeline.enrichment_pipeline import EnrichmentPipeline

async def enrich_music():
    # Initialize pipeline
    pipeline = EnrichmentPipeline(dry_run=False)

    # Process a single file
    audio_file = AudioFile(Path("/path/to/song.mp3"))
    result = await pipeline.enrich_file(audio_file)

    if result.success:
        print(f"✓ Successfully enriched: {result.file_path.name}")
        print(f"  Artist: {result.enriched_metadata.track.artist.name}")
        print(f"  Album: {result.enriched_metadata.track.album.title}")
        print(f"  Title: {result.enriched_metadata.track.title}")

    # Process a directory
    results, stats = await pipeline.enrich_directory(
        Path("/path/to/music"),
        recursive=True,
        skip_existing=True,
    )

    print(f"\nProcessing complete!")
    print(f"Success rate: {stats.success_rate():.1f}%")
    print(f"Files with artwork: {stats.artwork_added}")

# Run the async function
asyncio.run(enrich_music())
```

## 🏗️ Architecture

### Project Structure

```
Audio-Metadata-Completionist/
├── src/
│   ├── core/               # Core domain models
│   │   ├── audio_file.py   # Audio file abstraction
│   │   ├── metadata.py     # Metadata models with Pydantic
│   │   └── file_processor.py
│   ├── identification/     # Audio identification services
│   │   ├── acoustid_identifier.py
│   │   └── musicbrainz_client.py
│   ├── artwork/            # Artwork providers
│   │   ├── coverartarchive.py
│   │   ├── itunes.py
│   │   └── aggregator.py
│   ├── pipeline/           # Main enrichment pipeline
│   │   └── enrichment_pipeline.py
│   ├── utils/              # Utilities
│   │   ├── cache.py
│   │   ├── http_client.py
│   │   └── logging_config.py
│   ├── config.py           # Configuration with Pydantic Settings
│   └── cli.py              # Command-line interface
├── tests/                  # Comprehensive test suite
│   ├── unit/
│   └── integration/
├── main.py                 # CLI entry point
├── gui.py                  # GUI entry point
└── requirements.txt
```

### Workflow

1. **File Discovery**: Scan for supported audio files
2. **Fingerprinting**: Generate acoustic fingerprint using Chromaprint
3. **Identification**: Match fingerprint against AcousticID database
4. **Metadata Enrichment**: Fetch detailed metadata from MusicBrainz
5. **Artwork Download**: Search and download album artwork from multiple sources
6. **Metadata Writing**: Write enriched metadata and artwork to audio files

## 🎨 Supported Audio Formats

- **MP3** (.mp3) - ID3v2 tags
- **FLAC** (.flac) - Vorbis comments
- **M4A** (.m4a) - MP4 tags
- **OGG** (.ogg) - Vorbis comments
- **WAV** (.wav) - ID3v2 tags
- **WMA** (.wma) - ASF tags

## 🔧 Configuration

All configuration is done via environment variables in `.env` file:

```bash
# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/audio_metadata.log

# AcousticID (required)
ACOUSTID_API_KEY=your_api_key_here

# MusicBrainz
MUSICBRAINZ_CONTACT_EMAIL=your_email@example.com
MUSICBRAINZ_APP_NAME=AudioMetadataCompletionist
MUSICBRAINZ_APP_VERSION=1.0.0

# HTTP Configuration
HTTP_TIMEOUT=30
HTTP_MAX_RETRIES=3

# Cache
CACHE_ENABLED=true
CACHE_DIR=.cache
CACHE_TTL=86400

# Artwork
ARTWORK_MIN_SIZE=500
ARTWORK_MAX_SIZE=2000
ARTWORK_FORMAT=jpg

# Processing
MAX_WORKERS=4
BATCH_SIZE=10
```

## 🧪 Testing

Run the test suite:

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_metadata.py -v
```

## 🛠️ Development

### Setup Development Environment

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks (optional)
pre-commit install
```

### Code Quality

```bash
# Format code with black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Type checking with mypy
mypy src/

# Linting with pylint
pylint src/

# All checks
black src/ tests/ && isort src/ tests/ && mypy src/ && pylint src/
```

## 📊 Performance

- **Concurrent Processing**: Process multiple files in parallel (configurable)
- **Smart Caching**: Cache API responses to reduce network calls
- **Rate Limiting**: Respect API rate limits (MusicBrainz: 1 req/sec)
- **Efficient**: Typical processing time: 2-5 seconds per file (first run), <1 second (cached)

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [AcousticID](https://acoustid.org/) - Audio fingerprinting service
- [MusicBrainz](https://musicbrainz.org/) - Open music encyclopedia
- [Cover Art Archive](https://coverartarchive.org/) - Community-maintained album art repository
- [Mutagen](https://mutagen.readthedocs.io/) - Audio metadata library
- [Chromaprint](https://acoustid.org/chromaprint) - Audio fingerprinting library

## 🔍 Troubleshooting

### "audio could not be decoded" Error

If you see errors like `Fingerprinting error: audio could not be decoded` or `AcousticID identification failed: audio could not be decoded`, this means the required system dependencies are not installed.

**Solution:**

1. **Verify fpcalc is installed:**
   ```bash
   which fpcalc
   fpcalc -version
   ```

2. **Verify ffmpeg is installed:**
   ```bash
   which ffmpeg
   ffmpeg -version
   ```

3. **If missing, install the dependencies:**

   **Ubuntu/Debian:**
   ```bash
   sudo apt-get update
   sudo apt-get install -y libchromaprint-tools ffmpeg
   ```

   **macOS:**
   ```bash
   brew install chromaprint ffmpeg
   ```

   **Windows:**
   - Download Chromaprint: https://acoustid.org/chromaprint
   - Download FFmpeg: https://ffmpeg.org/download.html
   - Add both to your system PATH

### API Key Issues

If you get errors about missing API keys:

1. Register for a free AcousticID API key: https://acoustid.org/api-key
2. Add it to your `.env` file:
   ```bash
   ACOUSTID_API_KEY=your_api_key_here
   ```

### Unicode Path Issues

If you have issues with folders containing Unicode characters (Japanese, Chinese, etc.):

- **Use the GUI** (`python gui.py`) instead of the CLI for better Unicode path handling
- The GUI provides a visual folder browser that handles Unicode paths correctly

## 📧 Support

If you encounter any issues or have questions:

1. Check the [documentation](README.md) and [Troubleshooting](#-troubleshooting) section
2. Search [existing issues](https://github.com/Alfonso-Fierro/Audio-Metadata-Completionist/issues)
3. Create a [new issue](https://github.com/Alfonso-Fierro/Audio-Metadata-Completionist/issues/new)

## 🗺️ Roadmap

- [ ] Add more artwork providers (Spotify, Deezer, Last.fm)
- [ ] Support for additional audio formats
- [x] GUI interface
- [ ] Batch metadata editor
- [ ] Automatic folder organization
- [ ] Duplicate detection
- [ ] Lyrics fetching
- [ ] ReplayGain calculation

---

Made with ❤️ for music enthusiasts who value well-organized collections
