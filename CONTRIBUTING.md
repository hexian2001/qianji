# Contributing to Qianji

Thank you for your interest in contributing to Qianji! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.10+
- Playwright browsers installed
- Git

### Setup Steps

1. Fork and clone the repository:
```bash
git clone https://github.com/yourusername/qianji.git
cd qianji
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
playwright install chromium
```

4. Install pre-commit hooks:
```bash
pre-commit install
```

## Code Quality

We use several tools to maintain code quality:

### Formatting with Black
```bash
black qianji tests
```

### Linting with Ruff
```bash
ruff check qianji tests
ruff check --fix qianji tests  # Auto-fix issues
```

### Type Checking with MyPy
```bash
mypy qianji
```

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=qianji --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration
```

## Pull Request Process

1. **Create a branch**: `git checkout -b feature/your-feature-name`
2. **Make your changes**: Write code following our style guidelines
3. **Add tests**: Ensure your changes are covered by tests
4. **Run quality checks**: `black`, `ruff`, `mypy`, `pytest`
5. **Commit**: Use clear, descriptive commit messages
6. **Push**: `git push origin feature/your-feature-name`
7. **Create PR**: Open a pull request with a clear description

### Commit Message Format

```
type(scope): subject

body (optional)

footer (optional)
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test changes
- `chore`: Build process or auxiliary tool changes

Example:
```
feat(browser): add support for Firefox browser

Add Firefox browser support alongside existing Chromium support.
Includes profile configuration and launch options.

Closes #123
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints for all function signatures
- Write docstrings for all public functions and classes
- Keep functions focused and small
- Use meaningful variable names

## Testing Guidelines

- Write unit tests for all new functionality
- Maintain test coverage above 80%
- Use pytest fixtures for common setup
- Mock external dependencies in unit tests
- Write integration tests for API endpoints

## Documentation

- Update README.md if adding new features
- Update API documentation for endpoint changes
- Add docstrings to all public APIs
- Include examples in docstrings

## Reporting Issues

When reporting issues, please include:

1. **Description**: Clear description of the issue
2. **Steps to Reproduce**: Detailed steps to reproduce the problem
3. **Expected Behavior**: What you expected to happen
4. **Actual Behavior**: What actually happened
5. **Environment**: Python version, OS, Qianji version
6. **Logs**: Relevant log output or error messages

## Security

If you discover a security vulnerability, please email security@qianji.dev instead of opening a public issue.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
