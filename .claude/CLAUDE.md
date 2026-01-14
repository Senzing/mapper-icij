# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is `mapper-icij`, a Python script that converts ICIJ Offshore Leaks database files (Panama Papers, Paradise Papers, Bahamas Leaks, Offshore Leaks, Pandora Papers) to JSON format for loading into Senzing entity resolution.

## Development Setup

```bash
# Create virtual environment and install all dependencies
python -m venv ./venv
source ./venv/bin/activate
python -m pip install --upgrade pip
python -m pip install --group all .

# External dependency: mapper-base must be accessible
export PYTHONPATH=$PYTHONPATH:/path/to/mapper-base
```

## Common Commands

```bash
# Lint (matches CI workflow)
pylint $(git ls-files '*.py' ':!:docs/source/*')

# Other linting tools available
black src/
isort src/
flake8 src/
mypy src/
bandit -c pyproject.toml -r src/
```

## Running the Mapper

```bash
python src/icij_mapper.py -i /path/to/csv/files -o output.json [-l stats.json] [-a]
```

Required input CSV files: `nodes-entities.csv`, `nodes-intermediaries.csv`, `nodes-officers.csv`, `nodes-addresses.csv`, `nodes-others.csv`, `relationships.csv`

## Architecture

The mapper (`src/icij_mapper.py`) follows a single-script design:

1. Loads ICIJ CSV files into a temporary SQLite database for efficient querying
2. Creates SQL views to join node tables with relationships (edges)
3. Processes each node type (entity, intermediary, officer, address, other) sequentially
4. Outputs JSON lines format with Senzing entity resolution attributes

Key external dependency: Requires `base_mapper` from [mapper-base](https://github.com/Senzing/mapper-base) for company name detection and variant handling.

## Code Style

- Line length: 120 characters (black, flake8)
- Import sorting: isort with black profile
- See `pyproject.toml` for tool configurations and `.pylintrc` for additional pylint settings
