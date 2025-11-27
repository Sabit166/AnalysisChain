# Contributing to AnalysisChain

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/AnalysisChain.git`
3. Create a branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test your changes
6. Submit a pull request

## Development Setup

```powershell
# Clone and setup
git clone https://github.com/yourusername/AnalysisChain.git
cd AnalysisChain

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies (including dev dependencies)
pip install -r requirements.txt
pip install pytest pytest-asyncio black flake8
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Add docstrings to all public functions/classes
- Keep functions focused and concise

```python
# Good example
def load_document(file_path: Path) -> str:
    """
    Load document content from file
    
    Args:
        file_path: Path to the document
        
    Returns:
        Document text content
    """
    pass
```

## Testing

```powershell
# Run tests
pytest tests/ -v

# Run specific test
pytest tests/test_basic.py::TestDocumentLoader -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

## Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new features
3. **Ensure all tests pass**
4. **Update CHANGELOG** (if applicable)
5. **Follow commit message conventions**

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

Example:
```
feat(agent): Add multi-instruction support

- Allow switching between instruction files during session
- Maintain instruction history
- Update session state accordingly

Closes #123
```

## Areas for Contribution

### High Priority
- Additional LLM provider support (OpenAI, Cohere, etc.)
- Improved error handling and retry logic
- Performance optimizations
- Additional document formats (HTML, Markdown, etc.)

### Medium Priority
- Web UI for the agent
- Better logging and monitoring
- Advanced RAG strategies
- Batch processing optimizations

### Documentation
- More usage examples
- Video tutorials
- API documentation
- Translation to other languages

## Reporting Bugs

Use GitHub Issues and include:
- **Description**: Clear description of the bug
- **Steps to Reproduce**: Minimal steps to reproduce
- **Expected Behavior**: What should happen
- **Actual Behavior**: What actually happens
- **Environment**: OS, Python version, dependencies
- **Logs**: Relevant log output

## Feature Requests

Use GitHub Issues and include:
- **Use Case**: Why is this feature needed?
- **Proposed Solution**: How should it work?
- **Alternatives**: Other solutions considered
- **Additional Context**: Any other relevant information

## Questions?

- Open a GitHub Discussion
- Check existing issues
- Review documentation

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
