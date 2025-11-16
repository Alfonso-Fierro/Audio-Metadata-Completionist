# Contributing to Audio Metadata Completionist

Thank you for your interest in contributing to Audio Metadata Completionist! This document provides guidelines and instructions for contributing.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Reporting Bugs](#reporting-bugs)
- [Feature Requests](#feature-requests)

## 📜 Code of Conduct

This project adheres to a code of conduct that all contributors are expected to follow:

- Be respectful and inclusive
- Welcome newcomers and help them learn
- Focus on constructive criticism
- Accept responsibility for mistakes
- Prioritize the community's best interests

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Chromaprint/fpcalc
- Virtual environment tool (venv)

### Setup Development Environment

1. **Fork and clone the repository:**

```bash
git clone https://github.com/YOUR_USERNAME/Audio-Metadata-Completionist.git
cd Audio-Metadata-Completionist
```

2. **Create a virtual environment:**

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

4. **Configure environment:**

```bash
cp .env.example .env
# Edit .env and add your API keys
```

5. **Verify installation:**

```bash
pytest
python main.py --version
```

## 🔄 Development Workflow

### Branching Strategy

- `main` - Stable production branch
- `develop` - Development branch for integrating features
- `feature/*` - Feature branches
- `bugfix/*` - Bug fix branches
- `hotfix/*` - Urgent fixes for production

### Creating a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### Making Changes

1. Make your changes in the feature branch
2. Write or update tests
3. Update documentation as needed
4. Ensure all tests pass
5. Commit with clear, descriptive messages

## 💻 Coding Standards

### Python Style Guide

This project follows [PEP 8](https://pep8.org/) with the following tools:

- **black**: Code formatting (line length: 100)
- **isort**: Import sorting
- **mypy**: Static type checking
- **pylint**: Code linting

### Code Formatting

Before committing, format your code:

```bash
# Format with black
black src/ tests/

# Sort imports
isort src/ tests/

# Type checking
mypy src/

# Linting
pylint src/
```

Or run all at once:

```bash
make format  # If Makefile is provided
```

### Type Hints

All functions must have type hints:

```python
def process_file(file_path: Path, dry_run: bool = False) -> EnrichmentResult:
    """
    Process an audio file.

    Args:
        file_path: Path to the audio file
        dry_run: If True, don't write changes

    Returns:
        Enrichment result

    Raises:
        FileNotFoundError: If file doesn't exist
    """
    ...
```

### Documentation

- **Docstrings**: Use Google-style docstrings for all public functions, classes, and modules
- **Comments**: Explain "why", not "what"
- **README**: Update README.md for user-facing changes
- **CHANGELOG**: Add entry to CHANGELOG.md (if exists)

### Example Docstring

```python
class AudioFile:
    """
    Represents an audio file with metadata capabilities.

    This class provides methods for reading and writing audio metadata
    across multiple file formats using the mutagen library.

    Attributes:
        file_path: Path to the audio file

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is not supported
    """

    def write_metadata(self, metadata: Metadata) -> bool:
        """
        Write metadata to audio file.

        Args:
            metadata: Metadata to write

        Returns:
            True if successful

        Raises:
            RuntimeError: If write fails
        """
        ...
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_metadata.py

# Run with verbose output
pytest -v

# Run only failed tests
pytest --lf
```

### Writing Tests

- Write tests for all new features
- Maintain or improve code coverage (target: >80%)
- Use meaningful test names
- Follow AAA pattern: Arrange, Act, Assert

#### Example Test

```python
def test_merge_metadata():
    """Test merging metadata with higher confidence preferred."""
    # Arrange
    metadata1 = Metadata(
        track=TrackMetadata(title="Song"),
        confidence=0.7,
    )
    metadata2 = Metadata(
        track=TrackMetadata(title="Song", year=2024),
        confidence=0.9,
    )

    # Act
    merged = metadata1.merge_with(metadata2)

    # Assert
    assert merged.track.year == 2024
    assert merged.confidence == 0.9
```

### Test Structure

```
tests/
├── unit/                 # Unit tests (isolated components)
│   ├── test_metadata.py
│   ├── test_cache.py
│   └── test_config.py
├── integration/          # Integration tests (multiple components)
│   └── test_pipeline.py
└── conftest.py          # Shared fixtures
```

## 📤 Submitting Changes

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**

```
feat(artwork): add Spotify artwork provider

Implement new artwork provider that fetches album covers from
Spotify API with high-resolution images.

Closes #123
```

```
fix(identification): handle timeout errors gracefully

Add retry logic and better error handling for AcousticID API
timeouts to prevent pipeline failures.

Fixes #456
```

### Pull Request Process

1. **Update your branch:**

```bash
git checkout main
git pull upstream main
git checkout feature/your-feature
git rebase main
```

2. **Ensure tests pass:**

```bash
pytest
black --check src/ tests/
mypy src/
```

3. **Push to your fork:**

```bash
git push origin feature/your-feature
```

4. **Create Pull Request:**

- Go to GitHub and create a PR from your fork
- Fill out the PR template completely
- Link related issues
- Request review from maintainers

5. **PR Review:**

- Address reviewer feedback
- Keep PR focused and small
- Update based on comments
- Ensure CI passes

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] Commit messages follow convention
- [ ] No breaking changes (or documented)
- [ ] CHANGELOG.md updated (if exists)

## 🐛 Reporting Bugs

### Before Submitting

- Check existing issues
- Verify it's reproducible
- Collect relevant information

### Bug Report Template

```markdown
**Description:**
A clear description of the bug.

**To Reproduce:**
1. Step 1
2. Step 2
3. See error

**Expected Behavior:**
What you expected to happen.

**Actual Behavior:**
What actually happened.

**Environment:**
- OS: [e.g., Ubuntu 22.04]
- Python version: [e.g., 3.10.5]
- Project version: [e.g., 1.0.0]

**Logs:**
```
Paste relevant logs here
```

**Additional Context:**
Any other relevant information.
```

## 💡 Feature Requests

We welcome feature requests! Please provide:

1. **Use case**: Describe the problem you're trying to solve
2. **Proposed solution**: How you envision the feature working
3. **Alternatives**: Other solutions you've considered
4. **Additional context**: Any other relevant information

### Feature Request Template

```markdown
**Is your feature request related to a problem?**
A clear description of the problem.

**Describe the solution you'd like:**
A clear description of what you want to happen.

**Describe alternatives you've considered:**
Alternative solutions or features you've considered.

**Additional context:**
Any other context about the feature request.
```

## 🏗️ Architecture Guidelines

### Adding New Artwork Provider

1. Create new file in `src/artwork/`
2. Inherit from `ArtworkProvider` base class
3. Implement required methods: `search()`, `download()`, `name`
4. Add to `ArtworkAggregator` providers list
5. Write tests in `tests/unit/test_artwork.py`
6. Update documentation

### Adding New Identifier

1. Create new file in `src/identification/`
2. Inherit from `Identifier` base class
3. Implement required methods
4. Write comprehensive tests
5. Update documentation

## 📚 Additional Resources

- [Project README](README.md)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [Pytest Documentation](https://docs.pytest.org/)
- [Black Code Style](https://black.readthedocs.io/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

## 🤝 Getting Help

- **Questions**: Open a [Discussion](https://github.com/Alfonso-Fierro/Audio-Metadata-Completionist/discussions)
- **Issues**: Check [existing issues](https://github.com/Alfonso-Fierro/Audio-Metadata-Completionist/issues)
- **Chat**: Join our community chat (if available)

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Audio Metadata Completionist! 🎵
