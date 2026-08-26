import contextlib
import importlib
import io
import sys
import types
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENT_DIR = ROOT / "agent"
if str(AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(AGENT_DIR))


def _install_maa_stubs() -> None:
    maa = types.ModuleType("maa")
    agent = types.ModuleType("maa.agent")
    agent_server = types.ModuleType("maa.agent.agent_server")
    context = types.ModuleType("maa.context")
    custom_action = types.ModuleType("maa.custom_action")

    class AgentServer:
        @staticmethod
        def custom_action(name):
            def decorate(cls):
                cls.custom_action_name = name
                return cls

            return decorate

    class Context:
        pass

    class CustomAction:
        class RunArg:
            pass

    agent_server.AgentServer = AgentServer
    context.Context = Context
    custom_action.CustomAction = CustomAction

    sys.modules.setdefault("maa", maa)
    sys.modules.setdefault("maa.agent", agent)
    sys.modules.setdefault("maa.agent.agent_server", agent_server)
    sys.modules.setdefault("maa.context", context)
    sys.modules.setdefault("maa.custom_action", custom_action)


def _load_module():
    _install_maa_stubs()
    return importlib.import_module("custom.action.check_exploration_count")


def _argv_with_reco_detail(reco_detail):
    return types.SimpleNamespace(reco_detail=reco_detail)


def _reco_detail(best_text=None, raw_detail=None):
    best_result = (
        types.SimpleNamespace(text=best_text)
        if best_text is not None
        else None
    )
    return types.SimpleNamespace(
        best_result=best_result,
        filtered_results=[],
        all_results=[],
        raw_detail=raw_detail,
    )


def _run_action(action, argv):
    with contextlib.redirect_stdout(io.StringIO()):
        return action.run(None, argv)


class CheckExplorationCountTests(unittest.TestCase):
    def test_parse_left_count_accepts_slash_variants_and_prefixes(self):
        module = _load_module()

        for text in ("4/4", "探险次数：4/4", "４／４", "04/4"):
            with self.subTest(text=text):
                self.assertEqual(module._parse_left_count(text), 4)

    def test_parse_left_count_rejects_missing_slash_or_invalid_text(self):
        module = _load_module()

        for text in ("4", "", "没有次数", "探险次数：abc"):
            with self.subTest(text=text):
                self.assertIsNone(module._parse_left_count(text))

    def test_custom_action_returns_true_only_when_left_count_is_four(self):
        module = _load_module()
        action = module.CheckExplorationCount()

        true_argv = _argv_with_reco_detail(_reco_detail(best_text="探险次数：4/4"))
        self.assertTrue(_run_action(action, true_argv))

        for text in ("3/4", "14/4", "4", "无效文本"):
            with self.subTest(text=text):
                argv = _argv_with_reco_detail(_reco_detail(best_text=text))
                self.assertFalse(_run_action(action, argv))

    def test_custom_action_reads_raw_detail_fallback(self):
        module = _load_module()
        action = module.CheckExplorationCount()
        argv = _argv_with_reco_detail(_reco_detail(raw_detail={"text": "４／４"}))

        self.assertTrue(_run_action(action, argv))


if __name__ == "__main__":
    unittest.main()
