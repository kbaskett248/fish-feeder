import configparser
import fileinput
from pathlib import Path
import subprocess
import sys


def increment_poetry_version(*args):
    command = ["poetry", "version"]
    command.extend(args)
    subprocess.run(command, shell=True)


def read_name_and_version(file_path):
    config = configparser.ConfigParser()
    config.read("pyproject.toml")
    name = config.get("tool.poetry", "name")
    if name:
        name = name[1:-1].replace("-", "_")
    version = config.get("tool.poetry", "version")
    if version:
        version = version[1:-1]

    return name, version


def write_package_version(init_path, name: str, version: str):
    print(f"Writing version to {name}.__version__")
    for line in fileinput.input(init_path, inplace=True):
        if line.startswith("__version__") and line[11:].strip().startswith("="):
            print(f'__version__ = "{version}"')


def main(*args):
    project_dir = Path(__file__).parent.absolute()
    pyproject_path = project_dir / "pyproject.toml"
    if not pyproject_path.exists():
        sys.exit("Directory does not contain pyproject.toml")

    increment_poetry_version(*args)

    name, version = read_name_and_version(pyproject_path)

    if not name and version:
        sys.exit("Could not read name and/or version")

    init_path = project_dir / name / "__init__.py"
    if not init_path.exists():
        print(f"Package init file does not exist; not updating {name}.__version__")
        sys.exit()

    write_package_version(init_path, name, version)


if __name__ == "__main__":
    main(*sys.argv[1:])
