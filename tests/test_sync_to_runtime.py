import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import sync_to_runtime  # noqa: E402


class SyncToRuntimeTests(unittest.TestCase):
    def test_sync_replaces_resource_and_keeps_packaged_python(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir) / "runtime"
            dest.mkdir()
            (dest / "MFAAvalonia.exe").write_bytes(b"exe")
            (dest / "python").mkdir()
            (dest / "python" / "python.exe").write_bytes(b"py")
            old_resource = dest / "resource" / "old.txt"
            old_resource.parent.mkdir()
            old_resource.write_text("stale", encoding="utf-8")

            with mock.patch.object(sync_to_runtime, "configure_ocr_model"):
                sync_to_runtime.sync_to_runtime(dest, version="dev-local")

            interface = json.loads((dest / "interface.json").read_text(encoding="utf-8"))
            self.assertEqual(interface["agent"]["child_exec"], "./python/python.exe")
            self.assertEqual(interface["agent"]["child_args"], ["-u", "./agent/main.py"])
            self.assertEqual(interface["version"], "dev-local")
            self.assertTrue((dest / "resource" / "tasks" / "GameLifecycle.json").is_file())
            self.assertTrue((dest / "agent" / "main.py").is_file())
            self.assertTrue((dest / "python" / "python.exe").is_file())
            self.assertTrue((dest / "MFAAvalonia.exe").is_file())
            self.assertFalse(old_resource.exists())

    def test_sync_rejects_directory_without_exe(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            dest = Path(temp_dir)
            with self.assertRaises(FileNotFoundError):
                sync_to_runtime.sync_to_runtime(dest)


if __name__ == "__main__":
    unittest.main()
