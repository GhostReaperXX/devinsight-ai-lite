"""Allow the package to be run with: python -m issue_tool"""

from issue_tool.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
