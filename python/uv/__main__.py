#!/usr/bin/env python3
"""
Main entry point for running uv commands with templated environment variables.
"""

import os
import sys
from pathlib import Path

from . import find_uv_bin, run_with_template


def main():
    """
    Main entry point for templated uv commands:

    uvt sync - Process pyproject_template.toml and run uv sync
    """
    if len(sys.argv) < 2:
        print("Usage: python -m uv.template sync [args...]")
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


def _detect_virtualenv() -> str:
    """
    Find the virtual environment path for the current Python executable.
    """

    # If it's already set, then just use it
    value = os.getenv("VIRTUAL_ENV")
    if value:
        return value

    # Otherwise, check if we're in a venv
    venv_marker = os.path.join(sys.prefix, "pyvenv.cfg")

    if os.path.exists(venv_marker):
        return sys.prefix

    return ""


def _run() -> None:
    uv = os.fsdecode(find_uv_bin())

    env = os.environ.copy()
    venv = _detect_virtualenv()
    if venv:
        env.setdefault("VIRTUAL_ENV", venv)

    # Let `uv` know that it was spawned by this Python interpreter
    env["UV_INTERNAL__PARENT_INTERPRETER"] = sys.executable

    if sys.platform == "win32":
        import subprocess

        completed_process = subprocess.run([uv, *sys.argv[1:]], env=env)
        sys.exit(completed_process.returncode)
    else:
        os.execvpe(uv, [uv, *sys.argv[1:]], env=env)


if __name__ == "__main__":
    _run()
