
"""Build an Altomatic Windows executable using PyInstaller."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"
ICON_PATH = SRC_DIR / "app" / "resources" / "altomatic_icon.ico"
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"
SPEC_FILE = ROOT_DIR / "altomatic.spec"


def _run(cmd: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=cwd, check=True)


def _ensure_pyinstaller(python: str) -> None:
    try:
        subprocess.run([python, "-c", "import PyInstaller"], check=True, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        print("PyInstaller not found. Installing...")
        _run([python, "-m", "pip", "install", "pyinstaller"])


def _clean_previous_artifacts() -> None:
    for path in (DIST_DIR, BUILD_DIR, SPEC_FILE):
        if path.is_dir():
            shutil.rmtree(path)
        elif path.is_file():
            path.unlink()


def _collect_data_arguments() -> list[str]:
    separator = ";" if os.name == "nt" else ":"
    data_dir = SRC_DIR / "altomatic" / "data"
    resources_dir = SRC_DIR / "app" / "resources"
    args = [f"{data_dir}{separator}altomatic/data"]
    if resources_dir.exists():
        args.append(f"{resources_dir}{separator}app/resources")
    return args


def build_executable(python: str, name: str, clean: bool) -> Path:
    if not ICON_PATH.exists():
        # Create a dummy icon file
        ICON_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(ICON_PATH, "w") as f:
            f.write("")

    _ensure_pyinstaller(python)

    if clean:
        _clean_previous_artifacts()

    command = [
        python,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--windowed",
        "--onefile",
        "--name",
        name,
        "--icon",
        str(ICON_PATH),
        "--collect-data",
        "altomatic",
        "--collect-data",
        "app",
        *[arg for data_arg in _collect_data_arguments() for arg in ("--add-data", data_arg)],
        str(SRC_DIR / "altomatic" / "__main__.py"),
    ]

    print("Running:", " ".join(command))
    _run(command, cwd=ROOT_DIR)

    executable = DIST_DIR / f"{name}.exe"
    if not executable.exists():
        raise FileNotFoundError(f"Expected executable not found at {executable}")
    return executable


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the Altomatic Windows executable")
    parser.add_argument("--name", default="Altomatic", help="Output executable name")
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python interpreter to use for PyInstaller (defaults to current interpreter)",
    )
    parser.add_argument("--no-clean", action="store_true", help="Skip removing previous build artifacts")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    try:
        exe_path = build_executable(args.python, args.name, clean=not args.no_clean)
    except subprocess.CalledProcessError as exc:
        print("PyInstaller failed with exit code", exc.returncode)
        raise SystemExit(exc.returncode) from exc
    print(f"Executable created at: {exe_path}")


if __name__ == "__main__":
    main()
