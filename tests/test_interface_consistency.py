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
        self.assertIn("启动游戏_二次拉起", nodes)
        self.assertIn("关闭游戏", nodes)
        self.assertIn("启动游戏_确认进入村庄", nodes)
        self.assertIn("启动游戏_未能进入村庄", nodes)

    def test_start_game_wait_timeout_covers_app_launch(self):
        pipeline = check_interface.load_json(
            check_interface.PIPELINE_DIR / "启动游戏.json"
        )
        timeout = pipeline["启动游戏_处理界面"].get("timeout")
        self.assertGreaterEqual(
            timeout,
            60000,
            "启动游戏 must wait for the app UI instead of finishing on the launcher",
        )
        self.assertEqual(
            pipeline["启动游戏_处理界面"].get("on_error"),
            ["启动游戏_未能进入村庄"],
        )


if __name__ == "__main__":
    unittest.main()
