import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

import check_interface  # noqa: E402


class InterfaceConsistencyTests(unittest.TestCase):
    def test_interface_presets_and_pipeline_entries(self):
        errors = check_interface.validate()
        self.assertEqual(errors, [], "\n".join(errors))

    def test_start_and_stop_pipeline_nodes_exist(self):
        nodes = check_interface.collect_pipeline_nodes()
        self.assertIn("启动游戏", nodes)
        self.assertIn("关闭游戏", nodes)
        self.assertIn("启动游戏_确认进入村庄", nodes)


if __name__ == "__main__":
    unittest.main()
