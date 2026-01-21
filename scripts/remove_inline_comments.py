#!/usr/bin/env python3
"""Script to remove inline comments from Python files while preserving docstrings."""

import argparse
import ast
import io
import sys
import tokenize
from pathlib import Path
from typing import List, Set


def get_docstring_lines(source: str) -> Set[int]:
    """
    Identify line numbers that are part of docstrings using AST.

    Returns a set of line numbers (1-indexed) that contain docstrings.
    """
    docstring_lines = set()

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return docstring_lines

    for node in ast.walk(tree):
        docstring = ast.get_docstring(node, clean=False)
        if docstring is not None:
            if hasattr(node, 'body') and node.body:
                first_stmt = node.body[0]
                if isinstance(first_stmt, ast.Expr) and isinstance(first_stmt.value, ast.Constant):
                    start_line = first_stmt.lineno
                    end_line = first_stmt.end_lineno
                    if start_line and end_line:
                        for line_num in range(start_line, end_line + 1):
                            docstring_lines.add(line_num)

    return docstring_lines


def remove_comments(file_path: Path, dry_run: bool = False, verbose: bool = False) -> bool:
    """
    Remove inline comments from a Python file while preserving docstrings.

    Args:
        file_path: Path to the Python file to process
        dry_run: If True, don't modify the file, just report what would be done
        verbose: If True, print detailed information about processing

    Returns:
        True if processing was successful, False otherwise
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return False

    if not source:
        if verbose:
            print(f"Skipping empty file: {file_path}")
        return True

    try:
        docstring_lines = get_docstring_lines(source)
    except Exception as e:
        print(f"Error parsing AST for {file_path}: {e}", file=sys.stderr)
        return False

    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except tokenize.TokenError as e:
        print(f"Error tokenizing {file_path}: {e}", file=sys.stderr)
        return False

    lines = source.splitlines(keepends=True)
    if not lines:
        return True

    if not lines[-1].endswith('\n'):
        lines[-1] += '\n'

    modified_lines = []
    comments_removed = 0

    for line_idx, line in enumerate(lines):
        line_num = line_idx + 1

        if line_num == 1 and line.startswith('#!'):
            modified_lines.append(line)
            continue

        if line_num in docstring_lines:
            modified_lines.append(line)
            continue

        line_tokens = [t for t in tokens if t.start[0] == line_num]

        comment_tokens = [t for t in line_tokens if t.type == tokenize.COMMENT]

        if not comment_tokens:
            modified_lines.append(line)
            continue

        comment_token = comment_tokens[0]
        comment_start_col = comment_token.start[1]

        before_comment = line[:comment_start_col]

        after_comment = line[comment_token.end[1]:]

        stripped_before = before_comment.rstrip()

        if stripped_before:
            new_line = stripped_before + after_comment
        else:
            if after_comment.strip():
                new_line = line
            else:
                new_line = ''

        if new_line != line:
            comments_removed += 1
            if verbose:
                print(f"  Line {line_num}: Removing comment: {comment_token.string}")

        modified_lines.append(new_line)

    modified_source = ''.join(modified_lines)

    try:
        ast.parse(modified_source)
    except SyntaxError as e:
        print(f"Syntax error after comment removal in {file_path}: {e}", file=sys.stderr)
        return False

    if comments_removed == 0:
        if verbose:
            print(f"No comments found in {file_path}")
        return True

    if dry_run:
        print(f"[DRY RUN] Would remove {comments_removed} comment(s) from {file_path}")
        return True

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(modified_source)
        if verbose:
            print(f"Removed {comments_removed} comment(s) from {file_path}")
        return True
    except Exception as e:
        print(f"Error writing to {file_path}: {e}", file=sys.stderr)
        return False


def process_path(path: Path, dry_run: bool = False, verbose: bool = False) -> tuple[int, int]:
    """
    Process a file or directory, removing comments from Python files.

    Uses pathlib.Path.rglob("*.py") to recursively discover all Python files
    in the specified directory and its subdirectories. Includes all .py files
    without exclusions. Progress tracking shows "Processing file X of Y" for
    each file.

    Args:
        path: Path to file or directory to process
        dry_run: If True, don't modify files
        verbose: If True, print detailed information

    Returns:
        Tuple of (successful_count, failed_count)
    """
    successful = 0
    failed = 0

    if path.is_file():
        if path.suffix == '.py':
            if verbose:
                print(f"Processing: {path}")
            if remove_comments(path, dry_run, verbose):
                successful += 1
            else:
                failed += 1
        else:
            if verbose:
                print(f"Skipping non-Python file: {path}")
    elif path.is_dir():
        py_files = sorted(path.rglob('*.py'))
        total_files = len(py_files)

        print(f"Found {total_files} Python file(s) in {path}")

        for idx, py_file in enumerate(py_files, 1):
            print(f"Processing file {idx} of {total_files}: {py_file}")

            if remove_comments(py_file, dry_run, verbose):
                successful += 1
            else:
                failed += 1
    else:
        print(f"Path not found: {path}", file=sys.stderr)
        failed += 1

    return successful, failed


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Remove inline comments from Python files while preserving docstrings.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --dry-run file.py          # Preview changes to a single file
  %(prog)s --verbose baseplate/       # Process all files in baseplate/ directory
  %(prog)s --dry-run --verbose .      # Preview changes for entire repository
        """
    )

    parser.add_argument(
        'paths',
        nargs='*',
        default=['.'],
        help='Files or directories to process (default: current directory)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying files'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Print detailed information about processing'
    )

    args = parser.parse_args()

    total_successful = 0
    total_failed = 0

    for path_str in args.paths:
        path = Path(path_str)
        successful, failed = process_path(path, args.dry_run, args.verbose)
        total_successful += successful
        total_failed += failed

    print("\n" + "=" * 60)
    if args.dry_run:
        print(f"DRY RUN SUMMARY:")
    else:
        print(f"SUMMARY:")
    print(f"  Successfully processed: {total_successful} file(s)")
    print(f"  Failed: {total_failed} file(s)")
    print("=" * 60)

    if total_failed > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()
