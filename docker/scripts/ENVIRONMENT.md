# Development Environment Setup

This document outlines how to set up a development environment for working with the utility scripts in this project.

## Prerequisites

- Python 3.9 or higher
- pip (usually comes with Python)
- Git (for version control)

## Environment Setup

### Automatic Setup (Recommended)

We provide scripts to automatically set up your development environment:

#### Linux/macOS:

```bash
# Make the script executable
chmod +x setup_venv.sh

# Run the setup script
./setup_venv.sh
```

#### Windows:

```
# Run the setup script
setup_venv.bat
```

The setup scripts will:
1. Create a virtual environment in the `venv` directory
2. Install all required dependencies
3. Offer to install development tools

### Manual Setup

If you prefer to set up manually:

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Optional: Install development dependencies
pip install black isort mypy flake8 pytest pytest-cov
```

## Running Scripts

Always activate the virtual environment before running scripts:

```bash
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

Then you can run the scripts:

```bash
# Example: Running the translation script
python -m translation.translate_file --file path/to/your/file.po
```

## Docker Integration

The scripts can also be run inside Docker containers. The Docker setup is configured in the main project's docker-compose.yml file.

When running in Docker, the scripts will automatically detect the environment and use the appropriate settings.

## Development Tools

We use the following tools for development:

- **black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking
- **pytest**: Testing

### Running Linters

```bash
# Format code
black .

# Sort imports
isort .

# Run linting
flake8 .

# Run type checking
mypy .
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=.
```

## Keeping Dependencies Updated

To update dependencies:

```bash
# Update pip
pip install --upgrade pip

# Update all packages
pip install --upgrade -r requirements.txt
```

## Project-Specific Modules

Some modules have their own requirements files. If working on a specific module:

```bash
# Example: Install translation module dependencies
pip install -r translation/requirements.txt
``` 