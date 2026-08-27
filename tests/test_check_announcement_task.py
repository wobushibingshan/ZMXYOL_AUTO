import contextlib
import importlib
import io
import sys
import types
import unittest
from pathlib import Path
from unittest import mock


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
    return importlib.import_module("custom.action.check_announcement_task")


def _run_silently(callable_object, *args):
    with contextlib.redirect_stdout(io.StringIO()):
        return callable_object(*args)


class ClaimInitialAvailableTests(unittest.TestCase):
    def test_claim_page_rechecks_after_each_success_and_stops_at_slot_count(self):
        module = _load_module()
        slots = module.FIRST_PAGE_SLOTS

        with mock.patch.object(
            module,
            "_claim_first_available",
            side_effect=[True, True, True],
        ) as claim_first:
            claimed = _run_silently(module._claim_all_available, object(), slots)

        self.assertEqual(claimed, 2)
        self.assertEqual(claim_first.call_count, len(slots))

    def test_claim_page_stops_immediately_when_no_claim_is_available(self):
        module = _load_module()
        slots = module.FIRST_PAGE_SLOTS

        with mock.patch.object(
            module,
            "_claim_first_available",
            return_value=False,
        ) as claim_first:
            claimed = _run_silently(module._claim_all_available, object(), slots)

        self.assertEqual(claimed, 0)
        claim_first.assert_called_once()

    def test_initial_claim_scans_first_page_then_second_page(self):
        module = _load_module()
        context = object()
        calls = []

        with (
            mock.patch.object(
                module,
                "_go_first_page",
                side_effect=lambda actual_context: calls.append(
                    ("first_page", actual_context)
                ),
            ),
            mock.patch.object(
                module,
                "_go_second_page",
                side_effect=lambda actual_context: calls.append(
                    ("second_page", actual_context)
                ),
            ),
            mock.patch.object(
                module,
                "_claim_all_available",
                side_effect=lambda actual_context, slots: calls.append(
                    ("claim", actual_context, slots)
                )
                or len(slots),
            ),
        ):
            _run_silently(module._claim_initial_available, context)

        self.assertEqual(
            calls,
            [
                ("first_page", context),
                ("claim", context, module.FIRST_PAGE_SLOTS),
                ("second_page", context),
                ("claim", context, module.SECOND_PAGE_SLOTS),
            ],
        )

    def test_task_loop_clears_cache_then_runs_initial_claim_once(self):
        module = _load_module()
        context = object()
        argv = types.SimpleNamespace(
            custom_action_param='{"limit": 3, "max_rounds": 1}'
        )
        calls = []
        module._SKIPPED_TASKS.add("old-task")
        module._LAST_TASK_BY_SLOT["first:slot_1"] = "old-task"

        def record_initial_claim(actual_context):
            self.assertIs(actual_context, context)
            self.assertEqual(module._SKIPPED_TASKS, set())
            self.assertEqual(module._LAST_TASK_BY_SLOT, {})
            calls.append("initial_claim")

        with (
            mock.patch.object(
                module,
                "_claim_initial_available",
                side_effect=record_initial_claim,
            ) as initial_claim,
            mock.patch.object(
                module,
                "_go_first_page",
                side_effect=lambda actual_context: calls.append("round_first_page"),
            ),
            mock.patch.object(
                module,
                "_check_complete_limit",
                side_effect=lambda actual_context, limit: calls.append(
                    "check_limit"
                )
                or True,
            ),
        ):
            result = _run_silently(
                module.RunAnnouncementTaskLoop().run,
                context,
                argv,
            )

        self.assertTrue(result)
        initial_claim.assert_called_once_with(context)
        self.assertEqual(
            calls,
            ["initial_claim", "round_first_page", "check_limit"],
        )


if __name__ == "__main__":
    unittest.main()
