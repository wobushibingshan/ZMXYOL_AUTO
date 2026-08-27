import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import configure  # noqa: E402


class ConfigureOcrModelTests(unittest.TestCase):
    def _write_ocr(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        for name in configure.REQUIRED_OCR_FILES:
            (directory / name).write_bytes(name.encode("utf-8"))

    def test_skips_when_ocr_files_already_exist(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            assets = Path(temp_dir)
            self._write_ocr(configure.ocr_model_dir(assets))
            with mock.patch.object(configure, "download_ocr_model") as download:
                result = configure.configure_ocr_model(assets)

            download.assert_not_called()
            self.assertTrue(configure.ocr_model_ready(result))

    def test_copies_from_submodule_when_present(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            assets = Path(temp_dir)
            self._write_ocr(configure.submodule_ocr_dir(assets))
            with mock.patch.object(configure, "download_ocr_model") as download:
                result = configure.configure_ocr_model(assets)

            download.assert_not_called()
            self.assertTrue(configure.ocr_model_ready(result))
            self.assertEqual((result / "det.onnx").read_bytes(), b"det.onnx")

    def test_downloads_when_submodule_is_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            assets = Path(temp_dir)

            def fake_download(ocr_dir: Path, url: str = configure.OCR_ZIP_URL) -> None:
                self._write_ocr(ocr_dir)

            with mock.patch.object(
                configure, "download_ocr_model", side_effect=fake_download
            ) as download:
                result = configure.configure_ocr_model(assets)

            download.assert_called_once()
            self.assertTrue(configure.ocr_model_ready(result))


if __name__ == "__main__":
    unittest.main()
