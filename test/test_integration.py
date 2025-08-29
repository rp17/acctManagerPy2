"""
CRITICAL: View Package Integration Testing Framework

This module provides comprehensive testing for the view package integration,
including thread safety, MVC coordination, error handling, and multi-window management.

MANDATORY: All tests must verify thread safety and proper MVC integration.
"""

import unittest
import threading
import time
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from typing import Any

from view.view_manager import ViewManager, WindowCoordinator
from view.currency_manager import CurrencyManager
from view.error_handler import ViewErrorHandler, ThreadSafeErrorHandler, ErrorRecoveryManager
from view.base_view import View, FrameView, DialogView
from view.account_view import AccountView
from view.account_list_view import AccountListView


class ViewTestHelper:
    """
    CRITICAL: Testing utilities for view components
    MANDATORY: Provides common testing functionality
    """
    
    @staticmethod
    def create_test_view(view_class, mock_model=None, mock_controller=None):
        """
        MANDATORY: Create view for testing
        CRITICAL: Setup test environment with proper mocking
        """
        if mock_model is None:
            mock_model = Mock()
        if mock_controller is None:
            mock_controller = Mock()
        
        # CRITICAL: Setup test environment
        root = tk.Tk()
        root.withdraw()
        
        view = view_class(root, mock_controller)
        return view, root
    
    @staticmethod
    def simulate_model_event(view, event_type, event_data):
        """
        CRITICAL: Simulate model events for testing
        MANDATORY: Create realistic model events
        """
        mock_event = Mock()
        mock_event.kind = event_type
        mock_event.balance = event_data
        mock_event.agent_status = event_data
        
        view.model_changed(mock_event)
    
    @staticmethod
    def wait_for_gui_updates(view, timeout=1000):
        """
        MANDATORY: Wait for GUI updates to complete
        CRITICAL: Ensure thread-safe updates are processed
        """
        start_time = time.time()
        while time.time() - start_time < timeout / 1000:
            view.update()
            time.sleep(0.01)
    
    @staticmethod
    def create_mock_account():
        """Create a mock account for testing"""
        mock_account = Mock()
        mock_account.get_id.return_value = "test_account_001"
        mock_account.name = "Test Account"
        mock_account.account_id = "ACC001"
        mock_account.balance = Decimal("1000.00")
        return mock_account
    
    @staticmethod
    def create_mock_controller():
        """Create a mock controller for testing"""
        mock_controller = Mock()
        mock_controller.get_model.return_value = ViewTestHelper.create_mock_account()
        mock_controller.get_agent_status.return_value = {
            'deposit_agents': 2,
            'withdraw_agents': 1,
            'active_futures': 3
        }
        return mock_controller


class TestViewManager(unittest.TestCase):
    """Test ViewManager functionality"""
    
    def setUp(self):
        self.view_manager = ViewManager()
        self.mock_view = Mock()
        self.mock_view.model_changed = Mock()
    
    def test_register_view(self):
        """Test view registration"""
        self.view_manager.register_view("test_view", self.mock_view)
        self.assertEqual(self.view_manager.get_view_count("Mock"), 1)
        self.assertIsNotNone(self.view_manager.get_view("test_view"))
    
    def test_unregister_view(self):
        """Test view unregistration"""
        self.view_manager.register_view("test_view", self.mock_view)
        self.view_manager.unregister_view("test_view")
        self.assertEqual(self.view_manager.get_view_count("Mock"), 0)
        self.assertIsNone(self.view_manager.get_view("test_view"))
    
    def test_broadcast_model_event(self):
        """Test model event broadcasting"""
        self.view_manager.register_view("test_view", self.mock_view)
        
        mock_event = Mock()
        self.view_manager.broadcast_model_event(mock_event)
        
        # Verify event was received
        self.mock_view.model_changed.assert_called_with(mock_event)
    
    def test_thread_safety(self):
        """Test thread safety of view manager"""
        def register_views():
            for i in range(10):
                view = Mock()
                self.view_manager.register_view(f"view_{i}", view)
        
        def unregister_views():
            for i in range(10):
                self.view_manager.unregister_view(f"view_{i}")
        
        # Run operations in parallel
        threads = []
        for _ in range(5):
            threads.append(threading.Thread(target=register_views))
            threads.append(threading.Thread(target=unregister_views))
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify no crashes occurred
        stats = self.view_manager.get_view_statistics()
        self.assertIsInstance(stats, dict)


class TestWindowCoordinator(unittest.TestCase):
    """Test WindowCoordinator functionality"""
    
    def setUp(self):
        self.coordinator = WindowCoordinator()
        self.mock_account = ViewTestHelper.create_mock_account()
        self.mock_controller = ViewTestHelper.create_mock_controller()
    
    @patch('tkinter.Toplevel')
    def test_open_account_view(self, mock_toplevel):
        """Test account window opening"""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        
        window = self.coordinator.open_account_view(self.mock_account, self.mock_controller)
        
        self.assertIsNotNone(window)
        mock_window.title.assert_called()
        mock_window.geometry.assert_called()
    
    @patch('tkinter.Toplevel')
    def test_duplicate_window_prevention(self, mock_toplevel):
        """Test prevention of duplicate windows"""
        mock_window = Mock()
        mock_toplevel.return_value = mock_window
        
        # Open first window
        window1 = self.coordinator.open_account_view(self.mock_account, self.mock_controller)
        
        # Try to open duplicate
        window2 = self.coordinator.open_account_view(self.mock_account, self.mock_controller)
        
        # Should return the same window
        self.assertEqual(window1, window2)
        mock_window.lift.assert_called()
        mock_window.focus_force.assert_called()
    
    def test_window_statistics(self):
        """Test window statistics"""
        stats = self.coordinator.get_window_statistics()
        self.assertIsInstance(stats, dict)
        self.assertIn('account_windows', stats)
        self.assertIn('agent_windows', stats)
        self.assertIn('total_windows', stats)


class TestCurrencyManager(unittest.TestCase):
    """Test CurrencyManager functionality"""
    
    def setUp(self):
        self.currency_manager = CurrencyManager()
    
    def test_currency_conversion(self):
        """Test currency conversion accuracy"""
        # Test USD to EUR conversion
        amount = Decimal("100.00")
        converted = self.currency_manager.convert_amount(amount, "USD", "EUR")
        self.assertIsInstance(converted, Decimal)
        self.assertGreater(converted, 0)
    
    def test_same_currency_conversion(self):
        """Test conversion to same currency"""
        amount = Decimal("100.00")
        converted = self.currency_manager.convert_amount(amount, "USD", "USD")
        self.assertEqual(converted, amount)
    
    def test_currency_formatting(self):
        """Test currency formatting"""
        amount = Decimal("1234.56")
        formatted = self.currency_manager.format_amount(amount, "USD")
        self.assertEqual(formatted, "$1,234.56")
    
    def test_exchange_rate_update(self):
        """Test exchange rate updates"""
        mock_observer = Mock()
        self.currency_manager.register_observer(mock_observer)
        
        new_rate = Decimal("0.90")
        self.currency_manager.update_exchange_rate("EUR", new_rate)
        
        # Verify observer was notified
        mock_observer.on_currency_rate_changed.assert_called_with("EUR", new_rate)
    
    def test_thread_safety(self):
        """Test thread safety of currency operations"""
        def update_rates():
            for i in range(10):
                rate = Decimal(f"0.{80 + i}")
                self.currency_manager.update_exchange_rate("EUR", rate)
        
        def convert_amounts():
            for i in range(10):
                amount = Decimal(f"{100 + i}.00")
                self.currency_manager.convert_amount(amount, "USD", "EUR")
        
        # Run operations in parallel
        threads = []
        for _ in range(5):
            threads.append(threading.Thread(target=update_rates))
            threads.append(threading.Thread(target=convert_amounts))
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify no crashes occurred
        stats = self.currency_manager.get_currency_statistics()
        self.assertIsInstance(stats, dict)


class TestErrorHandler(unittest.TestCase):
    """Test ErrorHandler functionality"""
    
    def setUp(self):
        self.error_handler = ViewErrorHandler()
        self.mock_view = Mock()
    
    def test_error_handling(self):
        """Test basic error handling"""
        error = ValueError("Test error")
        ViewErrorHandler.handle_view_error(self.mock_view, error, "test_operation")
        
        # Verify error was logged
        error_log = self.error_handler.get_error_log()
        self.assertGreater(len(error_log), 0)
    
    def test_recovery_strategy(self):
        """Test error recovery strategies"""
        recovery_manager = ErrorRecoveryManager()
        
        # Test value error recovery
        error = ValueError("Invalid input")
        success = recovery_manager.attempt_recovery(self.mock_view, error)
        self.assertTrue(success)
    
    def test_thread_safe_error_handling(self):
        """Test thread-safe error handling"""
        thread_safe_handler = ThreadSafeErrorHandler(self.mock_view)
        
        error = ValueError("Thread error")
        thread_safe_handler.queue_error(error, "thread_operation")
        
        # Verify error was queued
        self.assertEqual(len(thread_safe_handler._error_queue), 1)
    
    def test_error_statistics(self):
        """Test error statistics collection"""
        error = ValueError("Test error")
        self.error_handler.log_error(error, "test_context", self.mock_view)
        
        stats = self.error_handler.get_error_statistics()
        self.assertIsInstance(stats, dict)
        self.assertIn('total_errors', stats)
        self.assertIn('error_types', stats)


class TestViewIntegration(unittest.TestCase):
    """Test complete view integration"""
    
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
    
    def tearDown(self):
        self.root.destroy()
    
    def test_account_view_integration(self):
        """Test AccountView integration with manager"""
        mock_account = ViewTestHelper.create_mock_account()
        mock_controller = ViewTestHelper.create_mock_controller()
        
        # Create view
        view = AccountView(self.root, mock_controller)
        
        # Test view registration
        view_manager = ViewManager()
        view_manager.register_view("test_account", view)
        
        # Test model event handling
        mock_event = Mock()
        mock_event.kind = "BALANCE_UPDATE"
        mock_event.balance = Decimal("2000.00")
        
        view.update_from_model(mock_event)
        
        # Verify view was registered
        self.assertEqual(view_manager.get_view_count("AccountView"), 1)
    
    def test_currency_integration(self):
        """Test currency manager integration with views"""
        currency_manager = CurrencyManager()
        mock_view = Mock()
        
        # Register view for currency updates
        currency_manager.register_observer(mock_view)
        
        # Update exchange rate
        currency_manager.update_exchange_rate("EUR", Decimal("0.90"))
        
        # Verify observer was notified
        mock_view.on_currency_rate_changed.assert_called_with("EUR", Decimal("0.90"))
    
    def test_error_handling_integration(self):
        """Test error handling integration"""
        error_handler = ViewErrorHandler()
        mock_view = Mock()
        
        # Register custom error callback
        def custom_callback(view, error):
            view.custom_error_handled = True
        
        error_handler.register_error_callback("ValueError", custom_callback)
        
        # Test error handling
        error = ValueError("Test error")
        success = error_handler.handle_specific_error(mock_view, error, "ValueError")
        
        self.assertTrue(success)
        self.assertTrue(hasattr(mock_view, 'custom_error_handled'))


class TestThreadSafety(unittest.TestCase):
    """Test thread safety of all components"""
    
    def test_concurrent_view_operations(self):
        """Test concurrent view operations"""
        view_manager = ViewManager()
        views = []
        
        def create_views():
            for i in range(5):
                view = Mock()
                view_manager.register_view(f"view_{i}", view)
                views.append(view)
        
        def destroy_views():
            for i in range(5):
                view_manager.unregister_view(f"view_{i}")
        
        # Run operations concurrently
        threads = []
        for _ in range(3):
            threads.append(threading.Thread(target=create_views))
            threads.append(threading.Thread(target=destroy_views))
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify no crashes
        stats = view_manager.get_view_statistics()
        self.assertIsInstance(stats, dict)
    
    def test_concurrent_currency_operations(self):
        """Test concurrent currency operations"""
        currency_manager = CurrencyManager()
        
        def convert_currencies():
            for i in range(10):
                amount = Decimal(f"{100 + i}.00")
                currency_manager.convert_amount(amount, "USD", "EUR")
        
        def update_rates():
            for i in range(10):
                rate = Decimal(f"0.{80 + i}")
                currency_manager.update_exchange_rate("EUR", rate)
        
        # Run operations concurrently
        threads = []
        for _ in range(5):
            threads.append(threading.Thread(target=convert_currencies))
            threads.append(threading.Thread(target=update_rates))
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify no crashes
        stats = currency_manager.get_currency_statistics()
        self.assertIsInstance(stats, dict)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2) 