import argparse
import shutil
import urllib.request
import zipfile
from pathlib import Path

PYTHON_VERSION = "3.12.10"
PYTHON_VERSION_PARTS = PYTHON_VERSION.split(".")
PYTHON_ABI_TAG = "".join(PYTHON_VERSION_PARTS[:2])
PYTHON_EMBED_URL = (
    f"https://www.python.org/ftp/python/{PYTHON_VERSION}/"
    f"python-{PYTHON_VERSION}-embed-amd64.zip"
)


def patch_pth(python_dir: Path) -> None:
    pth_files = list(python_dir.glob("python*._pth"))
    if not pth_files:
        raise FileNotFoundError(f"No python ._pth file found in {python_dir}")

    pth_path = pth_files[0]
    zip_name = f"python{PYTHON_ABI_TAG}.zip"
    if not (python_dir / zip_name).exists():
        raise FileNotFoundError(f"Embedded Python stdlib zip is missing: {zip_name}")

    pth_path.write_text(
        "\n".join(
            [
                zip_name,
                ".",
                "",
                "import site",
                "",
                "Lib",
                "Lib\\site-packages",
                "DLLs",
                "",
            ]
        ),
        encoding="utf-8",
    )


def setup_embed_python(install_dir: Path, url: str) -> None:
    python_dir = install_dir / "python"
    archive_path = install_dir / "python-embed.zip"

    if python_dir.exists():
        shutil.rmtree(python_dir)
    python_dir.mkdir(parents=True, exist_ok=True)
    install_dir.mkdir(parents=True, exist_ok=True)

    print(f"Downloading embedded Python from {url}")
    urllib.request.urlretrieve(url, archive_path)

    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(python_dir)
    archive_path.unlink(missing_ok=True)

    patch_pth(python_dir)
    print(f"Embedded Python installed to {python_dir}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--install-dir", default="install")
    parser.add_argument("--url", default=PYTHON_EMBED_URL)
    args = parser.parse_args()

    setup_embed_python(Path(args.install_dir).resolve(), args.url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
