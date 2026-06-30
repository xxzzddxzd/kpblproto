import unittest
from unittest.mock import patch
from types import SimpleNamespace

from modules.ghxs_manager import GHXSManager


class GHXSGuluFlowTest(unittest.TestCase):
    def test_guild_gulu_tasks_have_flow_config(self):
        for task_type_id in (201106, 205106):
            with self.subTest(task_type_id=task_type_id):
                config = GHXSManager.task_flow_config(task_type_id)
                self.assertIsNotNone(config)
                self.assertEqual(config["kind"], "gulu")
                self.assertEqual(config["times"], 2)

    def test_run_task_flow_dispatches_guild_gulu_task(self):
        class ProbeGHXSManager(GHXSManager):
            def __init__(self):
                self.account_name = "probe"
                self.showres = 0
                self.delay = 0
                self.ac_manager = None
                self.called = None

            def run_gulu_task(self, task_uuid=None, task_type_id=None):
                self.called = (task_uuid, task_type_id)
                return True

        ghxs = ProbeGHXSManager()

        self.assertTrue(ghxs.run_task_flow(task_uuid="task-uuid", task_type_id=201106))
        self.assertEqual(ghxs.called, ("task-uuid", 201106))

    def test_complete_verified_rejects_len_success_when_task_is_still_active(self):
        class ProbeGHXSManager(GHXSManager):
            def __init__(self):
                self.account_name = "probe"
                self.showres = 0
                self.delay = 0
                self.ac_manager = None
                self.complete_calls = 0

            def complete(self):
                self.complete_calls += 1
                return True

            def query(self):
                return SimpleNamespace(active_entries=[
                    SimpleNamespace(task_uuid="task-uuid", task_type_id=201106, progress=1)
                ])

        ghxs = ProbeGHXSManager()

        self.assertFalse(ghxs.complete_verified("task-uuid", 201106, delay_seconds=0))
        self.assertEqual(ghxs.complete_calls, 1)

    def test_wait_for_task_progress_runs_settle_callback_before_rechecking(self):
        class ProbeGHXSManager(GHXSManager):
            def __init__(self):
                self.account_name = "probe"
                self.showres = 0
                self.delay = 0
                self.ac_manager = None
                self.progresses = [1, 2]

            def query(self):
                progress = self.progresses.pop(0)
                return SimpleNamespace(active_entries=[
                    SimpleNamespace(task_uuid="task-uuid", task_type_id=201106, progress=progress)
                ])

        settle_calls = []
        ghxs = ProbeGHXSManager()

        self.assertTrue(ghxs.wait_for_task_progress(
            "task-uuid",
            201106,
            2,
            settle_callback=lambda: settle_calls.append("settle") or True,
            attempts=2,
        ))
        self.assertEqual(settle_calls, ["settle"])

    def test_available_task_entries_excludes_accepted_tasks(self):
        resp = SimpleNamespace(task_entries=[
            SimpleNamespace(task_uuid="available", status=0),
            SimpleNamespace(task_uuid="active", status=1),
            SimpleNamespace(task_uuid="handled", status=2),
        ])

        available = GHXSManager.available_task_entries(resp)

        self.assertEqual([task.task_uuid for task in available], ["available"])

    def test_gulu_task_refreshes_login_before_progress_check(self):
        class FakeAC:
            def __init__(self):
                self.login_calls = []

            def login(self, account_name, showloginres=0):
                self.login_calls.append((account_name, showloginres))
                return True

        class FakePartnerAC:
            def __init__(self, *args, **kwargs):
                pass

        class ProbeGHXSManager(GHXSManager):
            def __init__(self):
                self.account_name = "probe"
                self.showres = 0
                self.delay = 0
                self.ac_manager = FakeAC()
                self.progress_checked_after_login = False

            def _resolve_task_uuid(self, task_uuid, task_type_id):
                return task_uuid

            def _accept_resolved_task(self, task_uuid, task_type_id):
                return True

            def wait_for_task_progress(self, task_uuid, task_type_id, target_progress, settle_callback=None, attempts=3, delay_seconds=1):
                self.progress_checked_after_login = bool(self.ac_manager.login_calls)
                return True

            def complete_verified(self, task_uuid, task_type_id, attempts=2, delay_seconds=1):
                return True

            def claim_all_score_rewards(self):
                return 0

        ghxs = ProbeGHXSManager()
        with patch("modules.ghxs_manager.ACManager", FakePartnerAC), \
             patch("modules.gem_team_manager.run_gem_auto2", return_value=True):
            self.assertTrue(ghxs.run_gulu_task(task_uuid="task-uuid", task_type_id=202106))

        self.assertEqual(ghxs.ac_manager.login_calls, [("probe", 0)])
        self.assertTrue(ghxs.progress_checked_after_login)


if __name__ == "__main__":
    unittest.main()
