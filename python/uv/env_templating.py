import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional


def load_env_file(env_file_path: Path) -> Dict[str, str]:
    """Load environment variables from a .env file."""
    if not env_file_path.exists():
        return {}

    env_vars = {}
    with open(env_file_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Handle basic KEY=VALUE format (doesn't support quotes or multiline values)
            if "=" in line:
                key, value = line.split("=", 1)
                env_vars[key.strip()] = value.strip()

    return env_vars


def find_env_files(directory: Path) -> List[Path]:
    """Find all .env files in the specified directory."""
    return list(directory.glob(".env*"))


def replace_env_vars(content: str, env_vars: Dict[str, str]) -> str:
    """Replace environment variable placeholders in the content."""
    # Match patterns like {env:VARIABLE_NAME} or {env.VARIABLE_NAME}
    pattern = r"\{env[:.]([A-Za-z0-9_]+)\}"

    def replace_match(match):
        var_name = match.group(1)
        if var_name in env_vars:
            return env_vars[var_name]
        elif var_name in os.environ:
            return os.environ[var_name]
        else:
            # Keep the original placeholder if variable not found
            return match.group(0)

    return re.sub(pattern, replace_match, content)


def process_template(template_path: Path, project_dir: Path) -> Optional[Path]:
    """
    Process a pyproject_template.toml file:
    1. Collect environment variables from .env files
    2. Replace placeholders in the template
    3. Create a temporary pyproject.toml file

    Returns the path to the created pyproject.toml, or None if processing failed.
    """
    if not template_path.exists():
        return None

    # Load environment variables from .env files
    env_vars = {}
    for env_file in find_env_files(project_dir):
        env_vars.update(load_env_file(env_file))

    # Load template content
    with open(template_path, "r") as f:
        template_content = f.read()

    # Replace environment variables
    processed_content = replace_env_vars(template_content, env_vars)

    # Create output pyproject.toml
    pyproject_path = project_dir / "pyproject.toml"
    with open(pyproject_path, "w") as f:
        f.write(processed_content)

    return pyproject_path


def run_with_template(project_dir: Path, args: List[str]) -> int:
    """
    Run a command with a processed template:
    1. Process pyproject_template.toml to pyproject.toml
    2. Run the command
    3. Clean up pyproject.toml if it was created from template

    Returns the exit code from the command.
    """
    project_dir = Path(project_dir).resolve()
    template_path = project_dir / "pyproject_template.toml"
    pyproject_path = project_dir / "pyproject.toml"
    pyproject_existed = pyproject_path.exists()

    # Backup existing pyproject.toml if it exists
    backup_path = None
    if pyproject_existed:
        backup_path = project_dir / ".pyproject.toml.bak"
        shutil.copy2(pyproject_path, backup_path)

    try:
        # Process template
        if not template_path.exists():
            print(f"Template file not found: {template_path}", file=sys.stderr)
            return 1

        process_template(template_path, project_dir)

        # Run the command
        result = subprocess.run(args)
        return result.returncode

    finally:
        # Clean up
        if not pyproject_existed and pyproject_path.exists():
            pyproject_path.unlink()
        elif backup_path is not None and backup_path.exists():
            shutil.move(backup_path, pyproject_path)
