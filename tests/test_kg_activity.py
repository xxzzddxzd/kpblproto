import unittest
from types import SimpleNamespace
from unittest.mock import patch

from modules.kg_manager import KGManager
from modules.command_registry import _batch_kg


def _kg_response(board1_id=0, board2_id=0, field4=0, score=0, field8=0):
    return SimpleNamespace(
        boards=SimpleNamespace(
            board1=SimpleNamespace(board_id=board1_id),
            board2=SimpleNamespace(board_id=board2_id),
        ),
        field4=field4,
        mining_task_score=score,
        field8=field8,
    )


class KGActivityTest(unittest.TestCase):
    def test_activity_inactive_when_query_has_no_board_or_activity_fields(self):
        self.assertFalse(KGManager.is_activity_active(_kg_response()))

    def test_activity_active_when_query_has_board(self):
        self.assertTrue(KGManager.is_activity_active(_kg_response(board1_id=123)))

    def test_batch_kg_skips_accounts_when_activity_is_inactive(self):
        class FakeKGManager:
            is_activity_active = staticmethod(KGManager.is_activity_active)

            def __init__(self, account_name, ac_manager=None):
                pass

            def query_kg(self):
                return _kg_response()

        class FakeACManager:
            def __init__(self, *args, **kwargs):
                pass

        class FakeBatchManager:
            leader_account = "dh"
            showres = 0
            delay = 0

            def __init__(self):
                self.foreach_called = False

            def _for_each_account(self, func, desc, start_from=1):
                self.foreach_called = True

        mgr = FakeBatchManager()
        with patch("modules.command_registry.KGManager", FakeKGManager), \
             patch("modules.command_registry.ACManager", FakeACManager):
            self.assertTrue(_batch_kg(mgr, start_from=1, args=[]))

        self.assertFalse(mgr.foreach_called)


if __name__ == "__main__":
    unittest.main()
