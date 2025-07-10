#!/usr/bin/env python3
"""
MANDATORY: Comprehensive test suite for View layer
CRITICAL: Tests thread safety, GUI updates, error handling, and MVC integration
"""

import unittest
import tkinter as tk
from tkinter import ttk
import threading
import time
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

# Import our view components
from view.base_view import View, FrameView, DialogView, SpringUtilities
from view.account_view import AccountView
from view.account_list_view import AccountListView
from account_model import ModelEvent, EventKind, Account, AgentStatus
from mvc_controller import AccountController, AccountListController


class TestBaseView(unittest.TestCase):
    """Test base view functionality"""
    
    def setUp(self):
        """Setup test environment"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during tests
    
    def tearDown(self):
        """Cleanup test environment"""
        try:
            self.root.destroy()
        except:
            pass
    
    def test_view_interface(self):
        """Test View interface compliance"""
        # Test that View is abstract
        with self.assertRaises(TypeError):
            View()
    
    def test_frame_view_creation(self):
        """Test FrameView creation and basic functionality"""
        frame = FrameView(self.root)
        self.assertIsInstance(frame, ttk.Frame)
        self.assertIsInstance(frame, View)
    
    def test_frame_view_controller_assignment(self):
        """Test controller assignment"""
        frame = FrameView(self.root)
        controller = Mock()
        
        frame.set_controller(controller)
        self.assertEqual(frame.get_controller(), controller)
    
    def test_frame_view_error_display(self):
        """Test error display functionality"""
        frame = FrameView(self.root)
        
        with patch('tkinter.messagebox.showerror') as mock_error:
            frame.show_error("Test error")
            # Wait for after callback
            self.root.update()
            mock_error.assert_called_once_with("Error", "Test error")
    
    def test_frame_view_info_display(self):
        """Test info display functionality"""
        frame = FrameView(self.root)
        
        with patch('tkinter.messagebox.showinfo') as mock_info:
            frame.show_info("Test info")
            self.root.update()
            mock_info.assert_called_once_with("Information", "Test info")
    
    def test_frame_view_warning_display(self):
        """Test warning display functionality"""
        frame = FrameView(self.root)
        
        with patch('tkinter.messagebox.showwarning') as mock_warning:
            frame.show_warning("Test warning")
            self.root.update()
            mock_warning.assert_called_once_with("Warning", "Test warning")
    
    def test_frame_view_yes_no_dialog(self):
        """Test yes/no dialog functionality"""
        frame = FrameView(self.root)
        
        with patch('tkinter.messagebox.askyesno', return_value=True) as mock_ask:
            result = frame.ask_yes_no("Test question")
            self.root.update()
            mock_ask.assert_called_once_with("Confirm", "Test question")
            self.assertTrue(result)
    
    def test_frame_view_schedule_update(self):
        """Test thread-safe update scheduling"""
        frame = FrameView(self.root)
        update_called = threading.Event()
        
        def test_update():
            update_called.set()
        
        # Schedule update from different thread
        def schedule_from_thread():
            frame.schedule_update(test_update)
        
        thread = threading.Thread(target=schedule_from_thread)
        thread.start()
        thread.join()
        
        # Wait for update to be called
        self.root.update()
        self.assertTrue(update_called.is_set())
    
    def test_frame_view_grid_weights(self):
        """Test grid weight configuration"""
        frame = FrameView(self.root)
        
        frame.configure_grid_weights([1, 2, 3], [1, 1])
        
        # Verify grid weights were set
        self.assertEqual(frame.grid_rowconfigure(0), {'weight': 1})
        self.assertEqual(frame.grid_rowconfigure(1), {'weight': 2})
        self.assertEqual(frame.grid_rowconfigure(2), {'weight': 3})
    
    def test_dialog_view_creation(self):
        """Test DialogView creation"""
        dialog = DialogView(self.root, "Test Dialog")
        self.assertIsInstance(dialog, tk.Toplevel)
        self.assertIsInstance(dialog, View)
        dialog.destroy()
    
    def test_spring_utilities(self):
        """Test SpringUtilities helper methods"""
        frame = ttk.Frame(self.root)
        
        # Test make_grid
        SpringUtilities.make_grid(frame, 3, 2)
        self.assertEqual(frame.grid_rowconfigure(0), {'weight': 1})
        self.assertEqual(frame.grid_columnconfigure(0), {'weight': 1})
        
        # Test make_compact_grid
        SpringUtilities.make_compact_grid(frame, 2, 3)
        self.assertEqual(frame.grid_rowconfigure(0), {'weight': 0})
        self.assertEqual(frame.grid_columnconfigure(0), {'weight': 1})
        
        # Test create_separator
        separator = SpringUtilities.create_separator(frame, "horizontal")
        self.assertIsInstance(separator, ttk.Separator)
        
        # Test create_title_label
        title_label = SpringUtilities.create_title_label(frame, "Test Title")
        self.assertIsInstance(title_label, ttk.Label)
        
        # Test create_header_label
        header_label = SpringUtilities.create_header_label(frame, "Test Header")
        self.assertIsInstance(header_label, ttk.Label)
        
        # Test create_action_button
        action_button = SpringUtilities.create_action_button(frame, "Test", lambda: None)
        self.assertIsInstance(action_button, ttk.Button)


class TestAccountView(unittest.TestCase):
    """Test AccountView functionality"""
    
    def setUp(self):
        """Setup test environment"""
        self.root = tk.Tk()
        self.root.withdraw()
        
        # Create mock account and controller
        self.account = Account("Test Account", "TEST001", Decimal('100.00'))
        self.controller = Mock(spec=AccountController)
        self.controller.get_model.return_value = self.account
        self.controller.get_agent_status.return_value = {
            'deposit_agents': 0,
            'withdraw_agents': 0,
            'active_futures': 0
        }
    
    def tearDown(self):
        """Cleanup test environment"""
        try:
            self.root.destroy()
        except:
            pass
    
    def test_account_view_creation(self):
        """Test AccountView creation"""
        view = AccountView(self.root, self.controller)
        self.assertIsInstance(view, FrameView)
        self.assertEqual(view._controller, self.controller)
    
    def test_account_view_ui_build(self):
        """Test UI building"""
        view = AccountView(self.root, self.controller)
        
        # Check that balance display was created
        self.assertIsNotNone(view._balance_var)
        self.assertIsNotNone(view._status_var)
    
    def test_account_view_balance_update(self):
        """Test balance update from model event"""
        view = AccountView(self.root, self.controller)
        
        # Create balance update event
        event = ModelEvent(EventKind.BALANCE_UPDATE, balance=Decimal('150.00'))
        
        # Update view
        view.update_from_model(event)
        self.root.update()
        
        # Check that balance was updated
        self.assertEqual(view._balance_var.get(), "Balance: $150.00")
    
    def test_account_view_agent_status_update(self):
        """Test agent status update from model event"""
        view = AccountView(self.root, self.controller)
        
        # Create agent status update event
        status = AgentStatus(1, 2, 3)
        event = ModelEvent(EventKind.AGENT_STATUS_UPDATE, agent_status=status)
        
        # Update view
        view.update_from_model(event)
        self.root.update()
        
        # Verify controller was called to get updated status
        self.controller.get_agent_status.assert_called()
    
    def test_account_view_amount_input_validation(self):
        """Test amount input validation"""
        view = AccountView(self.root, self.controller)
        
        # Test valid amount
        with patch('tkinter.simpledialog.askstring', return_value="50.00"):
            amount = view._ask_amount("Test")
            self.assertEqual(amount, Decimal('50.00'))
        
        # Test empty input
        with patch('tkinter.simpledialog.askstring', return_value=""):
            with self.assertRaises(ValueError, msg="Amount required"):
                view._ask_amount("Test")
        
        # Test invalid amount
        with patch('tkinter.simpledialog.askstring', return_value="invalid"):
            with self.assertRaises(ValueError, msg="Invalid amount format"):
                view._ask_amount("Test")
        
        # Test negative amount
        with patch('tkinter.simpledialog.askstring', return_value="-10.00"):
            with self.assertRaises(ValueError, msg="Amount must be positive"):
                view._ask_amount("Test")
    
    def test_account_view_deposit_action(self):
        """Test deposit action"""
        view = AccountView(self.root, self.controller)
        
        with patch('tkinter.simpledialog.askstring', return_value="25.00"):
            view._on_deposit()
            self.controller.deposit.assert_called_once_with(Decimal('25.00'))
    
    def test_account_view_withdraw_action(self):
        """Test withdraw action"""
        view = AccountView(self.root, self.controller)
        
        with patch('tkinter.simpledialog.askstring', return_value="15.00"):
            view._on_withdraw()
            self.controller.withdraw.assert_called_once_with(Decimal('15.00'))
    
    def test_account_view_start_agents_action(self):
        """Test start agents action"""
        view = AccountView(self.root, self.controller)
        
        with patch.object(view, 'show_info') as mock_info:
            view._on_start_agents()
            
            # Verify agents were started
            self.controller.start_deposit_agent.assert_called_once_with(Decimal('10.00'), 20)
            self.controller.start_withdraw_agent.assert_called_once_with(Decimal('5.00'), 15)
            mock_info.assert_called_once_with("Agents started successfully")
    
    def test_account_view_agent_control_actions(self):
        """Test agent control actions"""
        view = AccountView(self.root, self.controller)
        
        # Test pause agents
        with patch.object(view, 'show_info') as mock_info:
            view._on_pause_agents()
            self.controller.pause_all_agents.assert_called_once()
            mock_info.assert_called_once_with("All agents paused")
        
        # Test resume agents
        with patch.object(view, 'show_info') as mock_info:
            view._on_resume_agents()
            self.controller.resume_all_agents.assert_called_once()
            mock_info.assert_called_once_with("All agents resumed")
        
        # Test stop agents
        with patch.object(view, 'show_info') as mock_info:
            view._on_stop_agents()
            self.controller.stop_all_agents.assert_called_once()
            mock_info.assert_called_once_with("All agents stopped")
    
    def test_account_view_error_handling(self):
        """Test error handling in actions"""
        view = AccountView(self.root, self.controller)
        
        # Test deposit error
        self.controller.deposit.side_effect = ValueError("Insufficient funds")
        
        with patch('tkinter.simpledialog.askstring', return_value="1000.00"):
            with patch.object(view, 'show_error') as mock_error:
                view._on_deposit()
                mock_error.assert_called_once_with("Insufficient funds")
        
        # Test withdraw error
        self.controller.withdraw.side_effect = ValueError("Insufficient balance")
        
        with patch('tkinter.simpledialog.askstring', return_value="50.00"):
            with patch.object(view, 'show_error') as mock_error:
                view._on_withdraw()
                mock_error.assert_called_once_with("Insufficient balance")


class TestAccountListView(unittest.TestCase):
    """Test AccountListView functionality"""
    
    def setUp(self):
        """Setup test environment"""
        self.root = tk.Tk()
        self.root.withdraw()
        
        # Create mock controller
        self.controller = Mock(spec=AccountListController)
        self.controller.get_agent_controller.return_value = Mock()
        self.controller.get_system_status.return_value = {
            'accounts': {'total_accounts': 2},
            'agent_test': {'test_running': False},
            'thread_pool': {'active_tasks': 0}
        }
    
    def tearDown(self):
        """Cleanup test environment"""
        try:
            self.root.destroy()
        except:
            pass
    
    def test_account_list_view_creation(self):
        """Test AccountListView creation"""
        view = AccountListView(self.root, self.controller)
        self.assertIsInstance(view, FrameView)
        self.assertEqual(view._controller, self.controller)
    
    def test_account_list_view_ui_build(self):
        """Test UI building"""
        view = AccountListView(self.root, self.controller)
        
        # Check that status display was created
        self.assertIsNotNone(view._status_var)
        self.assertEqual(view._status_var.get(), "Accounts: 0")
    
    def test_account_list_view_add_account(self):
        """Test adding account view"""
        view = AccountListView(self.root, self.controller)
        
        # Create mock account controller
        account_controller = Mock()
        account_controller.get_model.return_value = Account("Test", "TEST001", Decimal('100.00'))
        
        # Add account view
        view.add_account_view(account_controller)
        
        # Check that account view was added
        self.assertIn("TEST001", view._account_views)
        self.assertEqual(len(view._account_views), 1)
        self.assertEqual(view._status_var.get(), "Accounts: 1")
    
    def test_account_list_view_remove_account(self):
        """Test removing account view"""
        view = AccountListView(self.root, self.controller)
        
        # Add account first
        account_controller = Mock()
        account_controller.get_model.return_value = Account("Test", "TEST001", Decimal('100.00'))
        view.add_account_view(account_controller)
        
        # Remove account
        view.remove_account_view("TEST001")
        
        # Check that account view was removed
        self.assertNotIn("TEST001", view._account_views)
        self.assertEqual(len(view._account_views), 0)
        self.assertEqual(view._status_var.get(), "Accounts: 0")
    
    def test_account_list_view_add_account_action(self):
        """Test add account action"""
        view = AccountListView(self.root, self.controller)
        
        with patch('tkinter.simpledialog.askstring') as mock_ask:
            mock_ask.side_effect = ["TEST001", "Test Account", "100.00"]
            
            with patch.object(view, 'show_info') as mock_info:
                view._on_add_account()
                
                self.controller.add_account.assert_called_once_with("Test Account", "TEST001", Decimal('100.00'))
                mock_info.assert_called_once_with("Account 'Test Account' created successfully")
    
    def test_account_list_view_add_account_validation(self):
        """Test add account validation"""
        view = AccountListView(self.root, self.controller)
        
        # Test empty account ID
        with patch('tkinter.simpledialog.askstring', return_value=""):
            view._on_add_account()
            self.controller.add_account.assert_not_called()
        
        # Test empty name
        with patch('tkinter.simpledialog.askstring') as mock_ask:
            mock_ask.side_effect = ["TEST001", ""]
            view._on_add_account()
            self.controller.add_account.assert_not_called()
        
        # Test invalid balance
        with patch('tkinter.simpledialog.askstring') as mock_ask:
            mock_ask.side_effect = ["TEST001", "Test Account", "invalid"]
            
            with patch.object(view, 'show_error') as mock_error:
                view._on_add_account()
                mock_error.assert_called_once_with("Invalid balance format")
                self.controller.add_account.assert_not_called()
    
    def test_account_list_view_test_actions(self):
        """Test test control actions"""
        view = AccountListView(self.root, self.controller)
        
        # Test start test
        with patch.object(view, 'show_info') as mock_info:
            view._on_start_test()
            mock_info.assert_called_once_with("Concurrent test started")
        
        # Test stop test
        with patch.object(view, 'show_info') as mock_info:
            view._on_stop_test()
            mock_info.assert_called_once_with("Concurrent test stopped")
    
    def test_account_list_view_system_status(self):
        """Test system status display"""
        view = AccountListView(self.root, self.controller)
        
        with patch('tkinter.Toplevel') as mock_toplevel:
            mock_dialog = Mock()
            mock_toplevel.return_value = mock_dialog
            
            view._on_system_status()
            
            # Verify dialog was created
            mock_toplevel.assert_called_once()
            mock_dialog.title.assert_called_with("System Status")
    
    def test_account_list_view_format_system_status(self):
        """Test system status formatting"""
        view = AccountListView(self.root, self.controller)
        
        status = {
            'accounts': {
                'total_accounts': 2,
                'accounts': {
                    'TEST001': {
                        'name': 'Test Account 1',
                        'balance': Decimal('100.00'),
                        'agent_status': {'deposit_agents': 1, 'withdraw_agents': 0, 'active_futures': 1}
                    }
                }
            },
            'agent_test': {'test_running': True, 'total_agents': 5, 'active_agents': 3},
            'thread_pool': {'active_tasks': 2}
        }
        
        formatted = view._format_system_status(status)
        
        # Check that status was formatted correctly
        self.assertIn("Total Accounts: 2", formatted)
        self.assertIn("Test Account 1 (TEST001)", formatted)
        self.assertIn("Balance: $100.00", formatted)
        self.assertIn("Test Running: True", formatted)
        self.assertIn("Active Tasks: 2", formatted)
    
    def test_account_list_view_event_handlers(self):
        """Test event handler methods"""
        view = AccountListView(self.root, self.controller)
        
        # Test test started event
        view.on_test_started(5)
        self.root.update()
        self.assertEqual(view._status_var.get(), "Test running on 5 accounts")
        
        # Test test stopped event
        view.on_test_stopped()
        self.root.update()
        self.assertEqual(view._status_var.get(), "Test stopped")
        
        # Test emergency stop event
        view.on_emergency_stop()
        self.root.update()
        self.assertEqual(view._status_var.get(), "Emergency stop executed")
        
        # Test system shutdown event
        view.on_system_shutdown()
        self.root.update()
        self.assertEqual(view._status_var.get(), "System shutdown")


class TestViewThreadSafety(unittest.TestCase):
    """Test thread safety of view components"""
    
    def setUp(self):
        """Setup test environment"""
        self.root = tk.Tk()
        self.root.withdraw()
    
    def tearDown(self):
        """Cleanup test environment"""
        try:
            self.root.destroy()
        except:
            pass
    
    def test_concurrent_model_updates(self):
        """Test concurrent model updates from multiple threads"""
        controller = Mock()
        controller.get_model.return_value = Account("Test", "TEST001", Decimal('100.00'))
        controller.get_agent_status.return_value = {
            'deposit_agents': 0, 'withdraw_agents': 0, 'active_futures': 0
        }
        
        view = AccountView(self.root, controller)
        update_count = 0
        update_lock = threading.Lock()
        
        def update_from_thread():
            nonlocal update_count
            event = ModelEvent(EventKind.BALANCE_UPDATE, balance=Decimal('150.00'))
            view.update_from_model(event)
            
            with update_lock:
                update_count += 1
        
        # Start multiple threads updating the view
        threads = []
        for i in range(10):
            thread = threading.Thread(target=update_from_thread)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Update GUI to process all scheduled updates
        self.root.update()
        
        # Verify all updates were processed
        self.assertEqual(update_count, 10)
        self.assertEqual(view._balance_var.get(), "Balance: $150.00")
    
    def test_gui_responsiveness(self):
        """Test that GUI remains responsive during concurrent updates"""
        controller = Mock()
        controller.get_model.return_value = Account("Test", "TEST001", Decimal('100.00'))
        controller.get_agent_status.return_value = {
            'deposit_agents': 0, 'withdraw_agents': 0, 'active_futures': 0
        }
        
        view = AccountView(self.root, controller)
        updates_completed = threading.Event()
        
        def heavy_update():
            # Simulate heavy computation
            time.sleep(0.1)
            event = ModelEvent(EventKind.BALANCE_UPDATE, balance=Decimal('200.00'))
            view.update_from_model(event)
            updates_completed.set()
        
        # Start heavy update in background thread
        thread = threading.Thread(target=heavy_update)
        thread.start()
        
        # GUI should remain responsive
        start_time = time.time()
        while not updates_completed.is_set() and time.time() - start_time < 1.0:
            self.root.update()
            time.sleep(0.01)
        
        # Verify update was processed
        self.assertTrue(updates_completed.is_set())
        self.assertEqual(view._balance_var.get(), "Balance: $200.00")


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2) 