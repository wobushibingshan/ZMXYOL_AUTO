from __future__ import annotations

import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

ASSETS_DIR = Path(__file__).parent.parent.resolve() / "assets"
OCR_ZIP_URL = (
    "https://download.maafw.xyz/MaaCommonAssets/OCR/ppocr_v5/ppocr_v5-zh_cn.zip"
)
REQUIRED_OCR_FILES = ("det.onnx", "keys.txt", "rec.onnx")


def ocr_model_dir(assets_dir: Path | None = None) -> Path:
    return (assets_dir or ASSETS_DIR) / "resource" / "base" / "model" / "ocr"


def submodule_ocr_dir(assets_dir: Path | None = None) -> Path:
    return (assets_dir or ASSETS_DIR) / "MaaCommonAssets" / "OCR" / "ppocr_v5" / "zh_cn"


def ocr_model_ready(ocr_dir: Path) -> bool:
    return all((ocr_dir / name).is_file() for name in REQUIRED_OCR_FILES)


def _copy_ocr_files(source_dir: Path, ocr_dir: Path) -> None:
    ocr_dir.mkdir(parents=True, exist_ok=True)
    for name in REQUIRED_OCR_FILES:
        source = source_dir / name
        if not source.is_file():
            raise FileNotFoundError(source)
        shutil.copy2(source, ocr_dir / name)


def download_ocr_model(ocr_dir: Path, url: str = OCR_ZIP_URL) -> None:
    ocr_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="zmxyol-ocr-") as temp_dir:
        archive_path = Path(temp_dir) / "ppocr_v5-zh_cn.zip"
        print(f"Downloading OCR model from {url}")
        urllib.request.urlretrieve(url, archive_path)
        with zipfile.ZipFile(archive_path) as archive:
            archive.extractall(temp_dir)
        _copy_ocr_files(Path(temp_dir), ocr_dir)


def configure_ocr_model(assets_dir: Path | None = None) -> Path:
    resolved_assets = Path(assets_dir or ASSETS_DIR).resolve()
    ocr_dir = ocr_model_dir(resolved_assets)
    if ocr_model_ready(ocr_dir):
        print(f"Found existing OCR model in {ocr_dir}, skipping import.")
        return ocr_dir

    source_dir = submodule_ocr_dir(resolved_assets)
    if ocr_model_ready(source_dir):
        print(f"Copying OCR model from {source_dir}")
        _copy_ocr_files(source_dir, ocr_dir)
        return ocr_dir

    download_ocr_model(ocr_dir)
    if not ocr_model_ready(ocr_dir):
        raise FileNotFoundError(
            f"OCR model is still incomplete after download: {ocr_dir}"
        )
    print(f"OCR model installed to {ocr_dir}")
    return ocr_dir


if __name__ == "__main__":
    configure_ocr_model()
    print("OCR model configured.")
