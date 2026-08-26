import argparse
import importlib.metadata
from pathlib import Path


REQUIRED_MODULES = [
    "maa",
    "loguru",
    "PIL",
    "pytz",
    "requests",
    "pip",
    "win32_setctime",
]


def _has_module(site_packages: Path, module: str) -> bool:
    module_path = Path(*module.split("."))
    candidates = [
        site_packages / module_path,
        site_packages / f"{module_path.name}.py",
    ]
    return any(candidate.exists() for candidate in candidates)


def _find_pth(python_dir: Path) -> Path:
    pth_files = sorted(python_dir.glob("python*._pth"))
    if not pth_files:
        raise FileNotFoundError(f"No python ._pth file found in {python_dir}")
    return pth_files[0]


def _normalize_distribution_name(name: str) -> str:
    return name.lower().replace("_", "-")


def verify_embed_python(install_dir: Path) -> None:
    python_dir = install_dir / "python"
    site_packages = python_dir / "Lib" / "site-packages"

    if not python_dir.exists():
        raise FileNotFoundError(f"Embedded Python directory is missing: {python_dir}")
    if not site_packages.exists():
        raise FileNotFoundError(f"site-packages directory is missing: {site_packages}")

    pth_lines = [
        line.strip()
        for line in _find_pth(python_dir).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    pth_content = "\n".join(pth_lines)
    zip_entries = [line for line in pth_lines if line.endswith(".zip")]
    if not zip_entries:
        raise RuntimeError("python ._pth does not reference a stdlib zip")
    missing_zip_entries = [
        zip_entry for zip_entry in zip_entries if not (python_dir / zip_entry).exists()
    ]
    if missing_zip_entries:
        raise RuntimeError(
            "python ._pth references missing stdlib zip: "
            + ", ".join(missing_zip_entries)
        )

    for required_path in ("Lib", r"Lib\site-packages", "import site"):
        if required_path not in pth_content:
            raise RuntimeError(f"python ._pth is missing {required_path!r}")

    missing_modules = [
        module for module in REQUIRED_MODULES if not _has_module(site_packages, module)
    ]
    if missing_modules:
        raise RuntimeError(
            "Embedded Python is missing required modules: "
            + ", ".join(missing_modules)
        )

    distributions = {
        _normalize_distribution_name(distribution.metadata["Name"])
        for distribution in importlib.metadata.distributions(path=[str(site_packages)])
    }
    missing_distributions = [
        name
        for name in (
            "maafw",
            "loguru",
            "pillow",
            "pytz",
            "requests",
            "pip",
            "win32-setctime",
        )
        if name not in distributions
    ]
    if missing_distributions:
        raise RuntimeError(
            "Embedded Python is missing required distributions: "
            + ", ".join(missing_distributions)
        )

    print("Embedded Python verification passed.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--install-dir", default="install")
    args = parser.parse_args()

    verify_embed_python(Path(args.install_dir).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
