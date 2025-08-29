import unittest
from unittest.mock import MagicMock, patch
import sys
import types
import tkinter.messagebox

# Patch tkinter to avoid real GUI
with patch('tkinter.Tk'), patch('tkinter.Toplevel'), patch('tkinter.messagebox'), patch('tkinter.filedialog'), patch('tkinter.ttk.Combobox'), patch('tkinter.ttk.Button'), patch('tkinter.ttk.Frame'):
    from view.account_list_view import AccountListView as _AccountListView
    class AccountListView(_AccountListView):
        def update_from_model(self, *a, **kw):
            pass

class TestAccountListView(unittest.TestCase):
    def setUp(self):
        # Mock model and controller
        self.model = MagicMock()
        self.model.list_accounts.return_value = ['Alice', 'Bob']
        self.model.get_account_by_name.side_effect = lambda name: f"Account({name})"
        self.controller = MagicMock()
        self.controller.save_accounts = MagicMock()
        # Patch messagebox to avoid popups
        patcher_msgbox = patch('tkinter.messagebox')
        self.addCleanup(patcher_msgbox.stop)
        self.mock_msgbox = patcher_msgbox.start()
        # Patch sys.exit to prevent test exit
        patcher_exit = patch('sys.exit')
        self.addCleanup(patcher_exit.stop)
        self.mock_exit = patcher_exit.start()
        # Patch Toplevel to avoid real windows
        patcher_toplevel = patch('tkinter.Toplevel')
        self.addCleanup(patcher_toplevel.stop)
        patcher_toplevel.start()
        # Patch AccountView, AgentView, AccountController, AgentController, DepositAgent, WithdrawAgent
        self.patcher_account_view = patch('view.account_list_view.AccountView', MagicMock())
        self.patcher_agent_view = patch('view.account_list_view.AgentView', MagicMock())
        self.patcher_account_controller = patch('view.account_list_view.AccountController', MagicMock())
        self.patcher_agent_controller = patch('view.account_list_view.AgentController', MagicMock())
        self.patcher_deposit_agent = patch('view.account_list_view.DepositAgent', MagicMock())
        self.patcher_withdraw_agent = patch('view.account_list_view.WithdrawAgent', MagicMock())
        for p in [self.patcher_account_view, self.patcher_agent_view, self.patcher_account_controller, self.patcher_agent_controller, self.patcher_deposit_agent, self.patcher_withdraw_agent]:
            self.addCleanup(p.stop)
            p.start()
        # Create the view
        self.view = AccountListView(self.model, self.controller)

    def test_account_list_populated(self):
        # Account combo should be populated with model accounts
        self.assertEqual(self.view.account_combo['values'], ['Alice', 'Bob'])
        self.assertEqual(self.view.account_combo.current(), 0)

    def test_button_states(self):
        # All main buttons should be enabled if accounts exist
        for btn in [self.view.dollar_btn, self.view.euro_btn, self.view.yen_btn, self.view.deposit_agent_btn, self.view.withdraw_agent_btn]:
            btn.config.assert_any_call(state='normal')

    def test_get_selected_account(self):
        self.view.account_combo.current.return_value = 1
        self.view.account_combo['values'] = ['Alice', 'Bob']
        acc = self.view._get_selected_account()
        self.assertEqual(acc, 'Account(Bob)')

    def test_open_account_view(self):
        self.view.account_combo.current.return_value = 0
        self.view.account_combo['values'] = ['Alice', 'Bob']
        self.view._open_account_view('USD')
        # Should create a new AccountView and store it
        key = 'Account(Alice)_USD'
        self.assertIn(key, self.view._account_views)
        self.view._account_views[key].show.assert_called_once()

    def test_create_deposit_agent(self):
        self.view.account_combo.current.return_value = 0
        self.view.account_combo['values'] = ['Alice', 'Bob']
        self.view._create_deposit_agent()
        # Should create a new AgentView and show it
        from view.account_list_view import AgentView
        AgentView.return_value.show.assert_called_once()

    def test_create_withdraw_agent(self):
        self.view.account_combo.current.return_value = 0
        self.view.account_combo['values'] = ['Alice', 'Bob']
        self.view._create_withdraw_agent()
        from view.account_list_view import AgentView
        AgentView.return_value.show.assert_called_once()

    def test_save_accounts(self):
        self.view._save_accounts()
        self.controller.save_accounts.assert_called_once()
        self.mock_msgbox.showinfo.assert_called()

    def test_exit_application(self):
        self.view._exit_application()
        self.mock_exit.assert_called()

if __name__ == '__main__':
    unittest.main() 