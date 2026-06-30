import unittest

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


if __name__ == "__main__":
    unittest.main()
