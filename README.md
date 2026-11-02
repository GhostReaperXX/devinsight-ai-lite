# DevInsight AI Lite

An intelligent software issue tracker, built step by step during the field training.

This first version contains `issue_tool`, a command line utility that reads a messy CSV export
from an old issue tracker, cleans it, and lets you search, sort and summarise the issues.

## Requirements

- Python 3.14 or newer
- Git

The tool uses only the Python standard library, so there is nothing else to install.

## Getting started

```bash
git clone https://github.com/YOUR-USERNAME/devinsight-ai-lite.git
cd devinsight-ai-lite
python -m venv .venv
source .venv/Scripts/activate    # Git Bash on Windows
```

## Usage

Every command starts with the path of the CSV file:

```bash
python -m issue_tool data/issues_raw.csv clean                    # accepted and rejected rows
python -m issue_tool data/issues_raw.csv list --status open       # most urgent first
python -m issue_tool data/issues_raw.csv find 12                  # one issue by id
python -m issue_tool data/issues_raw.csv search login timeout     # issues with all these words
python -m issue_tool data/issues_raw.csv stats                    # summary numbers
python -m issue_tool data/issues_raw.csv export --format json     # writes out/report.json
```

## Project structure

| Path | Purpose |
|---|---|
| `issue_tool/models.py` | The `Issue` class and the allowed values |
| `issue_tool/errors.py` | The errors this tool raises on purpose |
| `issue_tool/cleaning.py` | Turns one untidy row into a validated `Issue` |
| `issue_tool/loader.py` | Reads the CSV file and separates good rows from bad rows |
| `issue_tool/search.py` | Linear search, binary search and dictionary lookups |
| `issue_tool/sorting.py` | Insertion sort, merge sort and triage order |
| `issue_tool/stats.py` | Counting and summary numbers |
| `issue_tool/reports.py` | Text and JSON report classes |
| `issue_tool/cli.py` | The command line interface |
| `benchmarks/compare_search.py` | Measures how search and sort times grow |

## Measuring the algorithms

```bash
python -m benchmarks.compare_search
```

## Contributing

Create a branch for each change, commit in small steps with clear messages, and open a pull
request. Never commit directly to `main`.
