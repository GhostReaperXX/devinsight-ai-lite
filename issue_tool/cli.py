"""The command line interface: turns typed arguments into function calls."""

import argparse
from pathlib import Path

from issue_tool.errors import IssueToolError
from issue_tool.loader import load_issues
from issue_tool.reports import REPORT_TYPES
from issue_tool.search import build_id_index, build_word_index, search_all_words
from issue_tool.sorting import sort_for_triage
from issue_tool.stats import summarize


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="issue_tool",
        description="Clean, search and summarise a CSV export of software issues.",
    )
    parser.add_argument("csv_file", type=Path, help="path to the exported CSV file")
    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser("clean", help="show how many rows were accepted and rejected")

    list_command = commands.add_parser("list", help="list issues, most urgent first")
    list_command.add_argument("--status", help="only this status, e.g. open")
    list_command.add_argument("--category", help="only this category, e.g. bug")

    find_command = commands.add_parser("find", help="show one issue by its id")
    find_command.add_argument("issue_id", type=int)

    search_command = commands.add_parser("search", help="find issues containing words")
    search_command.add_argument("words", nargs="+")

    commands.add_parser("stats", help="print summary numbers")

    export_command = commands.add_parser("export", help="write a report to a file")
    export_command.add_argument("--format", choices=sorted(REPORT_TYPES), default="json")
    export_command.add_argument("--out", type=Path, default=Path("out/report"))

    return parser


def run_clean(issues: list, rejected: list) -> None:
    print(f"Accepted: {len(issues)}")
    print(f"Rejected: {len(rejected)}")
    for error in rejected:
        print(f"  - {error}")


def run_list(issues: list, status: str | None, category: str | None) -> None:
    selected = [
        issue
        for issue in issues
        if (status is None or issue.status == status)
        and (category is None or issue.category == category)
    ]
    print(REPORT_TYPES["text"]().render(sort_for_triage(selected)))


def run_find(issues: list, issue_id: int) -> None:
    issue = build_id_index(issues).get(issue_id)
    if issue is None:
        raise IssueToolError(f"no issue with id {issue_id}")
    for name, value in issue.to_dict().items():
        print(f"{name:>12}: {value}")


def run_search(issues: list, words: list[str]) -> None:
    ids = search_all_words(build_word_index(issues), " ".join(words))
    matches = [issue for issue in issues if issue.issue_id in ids]
    print(REPORT_TYPES["text"]().render(sort_for_triage(matches)))


def run_stats(issues: list) -> None:
    for name, value in summarize(issues).items():
        print(f"{name:>12}: {value}")


def run_export(issues: list, report_format: str, out: Path) -> None:
    report = REPORT_TYPES[report_format]()
    target = out.with_suffix(report.file_suffix)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(report.render(issues), encoding="utf-8")
    print(f"Wrote {target}")


def main(arguments: list[str] | None = None) -> int:
    """Run one command and return an exit code: 0 for success, 1 for failure."""
    args = build_parser().parse_args(arguments)
    try:
        issues, rejected = load_issues(args.csv_file)
        if args.command == "clean":
            run_clean(issues, rejected)
        elif args.command == "list":
            run_list(issues, args.status, args.category)
        elif args.command == "find":
            run_find(issues, args.issue_id)
        elif args.command == "search":
            run_search(issues, args.words)
        elif args.command == "stats":
            run_stats(issues)
        elif args.command == "export":
            run_export(issues, args.format, args.out)
    except IssueToolError as error:
        print(f"Error: {error}")
        return 1
    return 0
