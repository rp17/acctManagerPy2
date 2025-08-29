import unittest
import threading
import tempfile
import os
import sys
from decimal import Decimal
from unittest.mock import MagicMock, patch
''' project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
 sys.path.insert(0, project_root) '''
from model.account_list import AccountList
from model.account_model import Account, ModelEvent, EventKind, AbstractModel

class DummyAgentImpl:
    @staticmethod
    def create_agent(account, agent_type, amount):
        return f"Agent({agent_type}, {amount})"
    @staticmethod
    def shutdown_and_await_termination():
        DummyAgentImpl.shutdown_called = True
        return True
DummyAgentImpl.shutdown_called = False

class TestAccountList(unittest.TestCase):
    def setUp(self):
        # Patch AgentImpl globally for all tests
        patcher = patch('model.account_list.AgentImpl', DummyAgentImpl)
        self.addCleanup(patcher.stop)
        patcher.start()
        # Create a temp file for persistence
        self.tempfile = tempfile.NamedTemporaryFile(delete=False)
        self.tempfile.close()
        self.account_list = AccountList(self.tempfile.name, use_tk=False)

    def tearDown(self):
        os.unlink(self.tempfile.name)

    def test_add_and_remove_account(self):
        acc = Account("TestUser", "A1", Decimal("100.00"))
        self.account_list.add_account(acc)
        self.assertIn("A1", [a.account_id for a in self.account_list])
        self.account_list.remove_account("A1")
        self.assertNotIn("A1", [a.account_id for a in self.account_list])

    def test_duplicate_account(self):
        acc = Account("TestUser", "A1", Decimal("100.00"))
        self.account_list.add_account(acc)
        with self.assertRaises(ValueError):
            self.account_list.add_account(acc)

    def test_get_account_by_name(self):
        acc = Account("TestUser", "A1", Decimal("100.00"))
        self.account_list.add_account(acc)
        found = self.account_list.get_account_by_name("TestUser")
        self.assertIs(found, acc)

    def test_list_accounts(self):
        acc1 = Account("User1", "A1", Decimal("100.00"))
        acc2 = Account("User2", "A2", Decimal("200.00"))
        self.account_list.add_account(acc1)
        self.account_list.add_account(acc2)
        names = self.account_list.list_accounts()
        self.assertIn("User1", names)
        self.assertIn("User2", names)

    def test_save_and_load(self):
        acc = Account("TestUser", "A1", Decimal("123.45"))
        self.account_list.add_account(acc)
        self.account_list.save()
        # Create a new AccountList and load
        new_list = AccountList(self.tempfile.name, use_tk=False)
        loaded = new_list.get_account("A1")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.name, "TestUser")
        self.assertEqual(loaded.balance, Decimal("123.45"))

    def test_thread_safety(self):
        accs = [Account(f"User{i}", f"A{i}", Decimal("10.00")) for i in range(10)]
        def add_remove():
            for acc in accs:
                self.account_list.add_account(acc)
            for acc in accs:
                self.account_list.remove_account(acc.account_id)
        threads = [threading.Thread(target=add_remove) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        # Should be empty or have no duplicates
        all_ids = [a.account_id for a in self.account_list]
        self.assertTrue(len(set(all_ids)) == len(all_ids))

    def test_observer_pattern(self):
        events = []
        class Listener:
            def __call__(self, event):
                events.append(event)
        listener = Listener()
        self.account_list.add_listener(listener)
        acc = Account("TestUser", "A1", Decimal("100.00"))
        self.account_list.add_account(acc)
        self.account_list.remove_account("A1")
        self.assertTrue(any(isinstance(e, ModelEvent) and e.kind == EventKind.BALANCE_UPDATE for e in events))

    def test_create_agent_and_shutdown(self):
        acc = Account("TestUser", "A1", Decimal("100.00"))
        self.account_list.add_account(acc)
        agent = self.account_list.create_agent("A1", "Deposit", Decimal("10.00"))
        self.assertEqual(agent, "Agent(Deposit, 10.00)")
        DummyAgentImpl.shutdown_called = False
        self.account_list.exit()
        self.assertTrue(DummyAgentImpl.shutdown_called)

if __name__ == "__main__":
    unittest.main() 