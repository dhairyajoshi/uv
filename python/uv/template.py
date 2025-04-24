#!/usr/bin/env python3
"""
Command-line interface for running uv with templated environment variables.
"""

import os
import sys
from pathlib import Path

from . import find_uv_bin, run_with_template


def main():
    """
    Command-line entry point for templated uv commands.
    """
    if len(sys.argv) < 2:
        print("Usage: uvt sync [args...]")
        return 1

    # Find uv binary
    uv_bin = find_uv_bin()
    if not uv_bin:
        print("Could not find uv binary", file=sys.stderr)
        return 1

    command = sys.argv[1]
    remaining_args = sys.argv[2:]

    # Currently only supports 'sync' command
    if command == "sync":
        project_dir = Path.cwd()
        args = [str(uv_bin), "sync"] + remaining_args
        return run_with_template(project_dir, args)
    else:
        print(f"Unsupported command: {command}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
