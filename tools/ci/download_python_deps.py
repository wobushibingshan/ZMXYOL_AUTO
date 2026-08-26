import argparse
import subprocess
import sys
from pathlib import Path

RUNTIME_PACKAGES = [
    # The Windows embeddable Python distribution does not include pip/ensurepip.
    "pip",
    # Loguru imports this module on Windows, but pip evaluates the marker on the
    # Linux CI host when installing with --platform win_amd64.
    "win32-setctime",
]


def download_python_deps(
    requirements: Path,
    dest: Path,
    target: Path | None,
    python_version: str,
    platform: str,
) -> None:
    if not requirements.exists():
        raise FileNotFoundError(requirements)

    dest.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        "-m",
        "pip",
        "download",
        "-r",
        str(requirements),
        "--dest",
        str(dest),
        "--only-binary=:all:",
        "--platform",
        platform,
        "--python-version",
        python_version,
        "--implementation",
        "cp",
        "--abi",
        f"cp{python_version}",
        *RUNTIME_PACKAGES,
    ]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True)

    if target is None:
        return

    target.mkdir(parents=True, exist_ok=True)
    install_cmd = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "-r",
        str(requirements),
        "--target",
        str(target),
        "--upgrade",
        "--only-binary=:all:",
        "--platform",
        platform,
        "--python-version",
        python_version,
        "--implementation",
        "cp",
        "--abi",
        f"cp{python_version}",
        *RUNTIME_PACKAGES,
    ]
    print("Running:", " ".join(install_cmd))
    subprocess.run(install_cmd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--requirements", default="requirements.txt")
    parser.add_argument("--dest", default="install/deps")
    parser.add_argument("--target", default="install/python/Lib/site-packages")
    parser.add_argument("--python-version", default="312")
    parser.add_argument("--platform", default="win_amd64")
    args = parser.parse_args()

    download_python_deps(
        Path(args.requirements).resolve(),
        Path(args.dest).resolve(),
        Path(args.target).resolve() if args.target else None,
        args.python_version,
        args.platform,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
