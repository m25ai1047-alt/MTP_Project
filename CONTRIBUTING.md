# Contributing to Automated RCA System

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## 🤝 How to Contribute

### Reporting Bugs

1. Check existing issues first
2. Use the bug report template
3. Include:
   - Python version
   - Error messages
   - Steps to reproduce
   - Expected vs actual behavior

### Suggesting Features

1. Check existing feature requests
2. Use the feature request template
3. Explain the use case
4. Provide examples if possible

### Submitting Code

#### Prerequisites

- Python 3.8+
- Familiarity with microservices and observability
- Understanding of RAG and LLMs (helpful but not required)

#### Setup Development Environment

```bash
# Fork and clone the repository
git clone https://github.com/yourusername/rca-system.git
cd rca-system

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Development Workflow

1. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make changes**
   - Follow the code style guidelines
   - Add tests for new functionality
   - Update documentation as needed

3. **Run tests**
   ```bash
   # Run all tests
   pytest

   # Run with coverage
   pytest --cov=src --cov-report=html

   # Run specific test
   pytest tests/test_anomaly_detector.py
   ```

4. **Code formatting**
   ```bash
   # Format code with black
   black src/ tests/

   # Check linting
   flake8 src/ tests/

   # Type checking
   mypy src/
   ```

5. **Commit changes**
   ```bash
   git add .
   git commit -m "feat: add support for Python code parsing"
   ```

6. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   # Then create a Pull Request on GitHub
   ```

## 📝 Code Style Guidelines

### Python Code Style

- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://black.readthedocs.io/) for formatting
- Maximum line length: 100 characters
- Use type hints where appropriate

### Example

```python
from typing import List, Dict, Optional

def analyze_error(error_log: str, top_k: int = 5) -> Dict[str, any]:
    """
    Analyze an error log and return root cause analysis.

    Args:
        error_log: The error log message
        top_k: Number of relevant code snippets to retrieve

    Returns:
        Dictionary containing analysis results
    """
    if not error_log:
        raise ValueError("error_log cannot be empty")

    # Implementation here
    return {"status": "success"}
```

### Documentation Style

- Use Google-style docstrings
- Include examples in docstrings
- Document all public APIs

## 🧪 Testing Guidelines

### Writing Tests

- Place tests in `tests/` directory
- Mirror the source directory structure
- Use descriptive test names
- Follow Arrange-Act-Assert pattern

### Example Test

```python
import pytest
from src.rca_agent import RCAAnalyzer

def test_rca_analyzer_initialization():
    """Test that RCAAnalyzer initializes correctly."""
    analyzer = RCAAnalyzer(use_enhanced=False)
    assert analyzer.enhanced_mode is False
    assert analyzer.retriever is not None

def test_rca_analyze_with_null_pointer():
    """Test RCA analysis of NullPointerException."""
    analyzer = RCAAnalyzer(use_enhanced=False)
    result = analyzer.analyze(
        "ERROR: NullPointerException at UserService.getUser"
    )
    assert "analysis" in result
    assert "keywords_extracted" in result
```

### Test Coverage

- Aim for >80% code coverage
- Focus on critical paths
- Test edge cases and error conditions

## 📚 Documentation Guidelines

### What to Document

- All public functions and classes
- Complex algorithms
- Configuration options
- Breaking changes

### Where to Document

- **Code**: Docstrings
- **Features**: `docs/guides/`
- **Architecture**: `docs/architecture/`
- **API**: `docs/api.md`

## 🎯 Feature Guidelines

### Small Features

- Create a branch: `feature/feature-name`
- Add tests
- Update documentation
- Submit PR

### Large Features

1. **Proposal**: Open an issue with the "proposal" label
2. **Discussion**: Get feedback from maintainers
3. **Design**: Create a design document in `docs/proposals/`
4. **Implementation**: Break into smaller PRs
5. **Review**: Each PR reviewed separately

## 🐛 Bug Fix Guidelines

1. **Verify**: Reproduce the bug
2. **Test**: Add a failing test
3. **Fix**: Implement the fix
4. **Verify**: Ensure test passes
5. **Regression**: Check for side effects

## 📦 Release Process

Maintainers will:

1. Update version in `setup.py`
2. Update `CHANGELOG.md`
3. Create git tag
4. Build and publish to PyPI
5. Release on GitHub

## 💬 Communication

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and ideas
- **Pull Requests**: Code reviews and discussions

## 🏷️ Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

### Examples

```bash
feat: add support for Python code indexing
fix: handle null pointer exceptions in RCA
docs: update installation guide
test: add integration tests for anomaly detector
```

## 🌟 Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Credited in significant features

## ❓ Questions?

- Open a GitHub Discussion
- Email: your-email@example.com
- Check existing issues and discussions

---

Thank you for contributing! 🎉
