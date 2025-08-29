import unittest
import threading
import time
from decimal import Decimal
from concurrent.futures import Future
from unittest.mock import Mock, MagicMock

from controller.mvc_controller import (
    Controller, AbstractController, AccountController, 
    AccountListController, AgentController, MainController,
    create_account_controller, create_account_list_controller,
    create_agent_controller, create_main_controller
)
from model.account_model import (
    Account, AgentStatus, OverdrawException, ModelEvent, EventKind
)
from model.agent_system import AgentImpl


class MockView:
    """Mock view for testing controllers"""
    def __init__(self):
        self.controller = None
        self.errors = []
        self.updates = []
        self.account_views = {}
        self.test_events = []
    
    def set_controller(self, controller):
        self.controller = controller
    
    def update_from_model(self, event):
        self.updates.append(event)
    
    def show_error(self, error_message):
        self.errors.append(error_message)
    
    def add_account_view(self, controller):
        account = controller.get_model()
        self.account_views[account.account_id] = controller
    
    def remove_account_view(self, account_id):
        if account_id in self.account_views:
            del self.account_views[account_id]
    
    def on_test_started(self, account_count):
        self.test_events.append(f"test_started_{account_count}")
    
    def on_test_stopped(self):
        self.test_events.append("test_stopped")
    
    def on_emergency_stop(self):
        self.test_events.append("emergency_stop")
    
    def on_system_shutdown(self):
        self.test_events.append("system_shutdown")


class TestController(unittest.TestCase):
    """Test base controller functionality"""
    
    def setUp(self):
        """Setup test environment"""
        AgentImpl.reset_executor()
        self.view = MockView()
        self.account = Account("Test Account", "TEST001", Decimal("1000.00"), force_direct_notify=True)
    
    def tearDown(self):
        """Cleanup after tests"""
        AgentImpl.shutdown_executor()
    
    def test_abstract_controller_creation(self):
        """Test AbstractController creation and basic functionality"""
        controller = AbstractController()
        
        # Test initial state
        self.assertIsNone(controller.get_model())
        self.assertIsNone(controller.get_view())
        
        # Test model assignment
        controller.set_model(self.account)
        self.assertEqual(controller.get_model(), self.account)
        
        # Test view assignment
        controller.set_view(self.view)
        self.assertEqual(controller.get_view(), self.view)
        self.assertEqual(self.view.controller, controller)
    
    def test_controller_model_listener(self):
        """Test controller properly handles model change notifications"""
        controller = AbstractController()
        controller.set_model(self.account)
        controller.set_view(self.view)
        
        # Trigger model change
        self.account.deposit(Decimal("100.00"))
        
        # Verify view was notified
        self.assertGreater(len(self.view.updates), 0)
        self.assertEqual(self.view.updates[0].kind, EventKind.BALANCE_UPDATE)
    
    def test_controller_error_handling(self):
        """Test controller error handling"""
        controller = AbstractController()
        controller.set_view(self.view)
        
        # Test error handling
        controller._handle_error("Test error message")
        
        # Verify error was logged and view was notified
        self.assertIn("Test error message", self.view.errors)


class TestAccountController(unittest.TestCase):
    """Test AccountController functionality"""
    
    def setUp(self):
        """Setup test environment"""
        AgentImpl.reset_executor()
        self.view = MockView()
        self.account = Account("Test Account", "TEST001", Decimal("1000.00"), force_direct_notify=True)
        self.controller = AccountController(self.account)
        self.controller.set_view(self.view)
    
    def tearDown(self):
        """Cleanup after tests"""
        self.controller.stop_all_agents()
        AgentImpl.shutdown_executor()
    
    def test_account_controller_creation(self):
        """Test AccountController creation"""
        self.assertEqual(self.controller.get_model(), self.account)
        self.assertEqual(self.controller.get_view(), self.view)
    
    def test_deposit_operation(self):
        """Test deposit operation"""
        initial_balance = self.account.balance
        
        # Test valid deposit
        self.controller.deposit(Decimal("100.00"))
        self.assertEqual(self.account.balance, initial_balance + Decimal("100.00"))
        
        # Test invalid deposit
        self.controller.deposit(Decimal("-50.00"))
        self.assertIn("Deposit amount must be positive", self.view.errors[0])
    
    def test_withdraw_operation(self):
        """Test withdraw operation"""
        initial_balance = self.account.balance
        
        # Test valid withdrawal
        self.controller.withdraw(Decimal("100.00"))
        self.assertEqual(self.account.balance, initial_balance - Decimal("100.00"))
        
        # Test invalid withdrawal
        self.controller.withdraw(Decimal("-50.00"))
        self.assertIn("Withdrawal amount must be positive", self.view.errors[0])
        
        # Test overdraw
        self.controller.withdraw(Decimal("2000.00"))
        self.assertIn("Insufficient funds", self.view.errors[1])
    
    def test_transfer_operation(self):
        """Test transfer operation"""
        target_account = Account("Target", "TARGET001", Decimal("500.00"), force_direct_notify=True)
        initial_source_balance = self.account.balance
        initial_target_balance = target_account.balance
        
        # Test valid transfer
        self.controller.transfer(target_account, Decimal("100.00"))
        self.assertEqual(self.account.balance, initial_source_balance - Decimal("100.00"))
        self.assertEqual(target_account.balance, initial_target_balance + Decimal("100.00"))
        
        # Test invalid transfer
        self.controller.transfer(None, Decimal("100.00"))
        self.assertIn("Target account cannot be None", self.view.errors[0])
    
    def test_agent_management(self):
        """Test agent management functionality"""
        # Start deposit agent
        self.controller.start_deposit_agent(Decimal("10.00"), 3)
        
        # Start withdraw agent
        self.controller.start_withdraw_agent(Decimal("5.00"), 2)
        
        # Wait for agents to complete
        time.sleep(2.0)
        
        # Check agent status
        status = self.controller.get_agent_status()
        self.assertGreaterEqual(status['deposit_agents'], 1)
        self.assertGreaterEqual(status['withdraw_agents'], 1)
    
    def test_agent_pause_resume(self):
        """Test agent pause and resume functionality"""
        # Start agents
        self.controller.start_deposit_agent(Decimal("10.00"), 10)
        
        # Let them run for a bit
        time.sleep(0.5)
        
        # Pause agents
        self.controller.pause_all_agents()
        
        # Resume agents
        self.controller.resume_all_agents()
        
        # Wait for completion
        time.sleep(3.0)
        
        # Verify completion
        status = self.controller.get_agent_status()
        self.assertGreaterEqual(status['deposit_agents'], 1)
    
    def test_agent_stop(self):
        """Test agent stop functionality"""
        # Start agents
        self.controller.start_deposit_agent(Decimal("1.00"), 100)
        
        # Let them run for a bit
        time.sleep(0.5)
        
        # Stop agents
        self.controller.stop_all_agents()
        
        # Verify agents are stopped
        status = self.controller.get_agent_status()
        self.assertEqual(status['active_futures'], 0)


class TestAccountListController(unittest.TestCase):
    """Test AccountListController functionality"""
    
    def setUp(self):
        """Setup test environment"""
        AgentImpl.reset_executor()
        self.view = MockView()
        self.controller = AccountListController()
        self.controller.set_view(self.view)
    
    def tearDown(self):
        """Cleanup after tests"""
        # Stop all agents and remove accounts
        for account_controller in self.controller.get_all_accounts():
            account_controller.stop_all_agents()
        AgentImpl.shutdown_executor()
    
    def test_account_list_controller_creation(self):
        """Test AccountListController creation"""
        self.assertIsNone(self.controller.get_model())
        self.assertEqual(self.controller.get_view(), self.view)
    
    def test_add_account(self):
        """Test adding accounts"""
        # Add account
        account_controller = self.controller.add_account("Test Account", "TEST001", Decimal("1000.00"))
        
        # Verify account was added
        self.assertIsNotNone(account_controller)
        self.assertEqual(account_controller.get_model().name, "Test Account")
        self.assertEqual(account_controller.get_model().account_id, "TEST001")
        
        # Verify view was notified
        self.assertIn("TEST001", self.view.account_views)
        
        # Test duplicate account ID
        with self.assertRaises(ValueError):
            self.controller.add_account("Another Account", "TEST001", Decimal("500.00"))
    
    def test_remove_account(self):
        """Test removing accounts"""
        # Add account
        self.controller.add_account("Test Account", "TEST001", Decimal("1000.00"))
        
        # Remove account
        self.controller.remove_account("TEST001")
        
        # Verify account was removed
        self.assertIsNone(self.controller.get_account_controller("TEST001"))
        self.assertNotIn("TEST001", self.view.account_views)
        
        # Test removing non-existent account
        with self.assertRaises(ValueError):
            self.controller.remove_account("NONEXISTENT")
    
    def test_transfer_between_accounts(self):
        """Test transfer between accounts"""
        # Add accounts
        self.controller.add_account("Source", "SRC001", Decimal("1000.00"))
        self.controller.add_account("Target", "TGT001", Decimal("500.00"))
        
        # Perform transfer
        self.controller.transfer_between_accounts("SRC001", "TGT001", Decimal("200.00"))
        
        # Verify transfer
        source_account = self.controller.get_account_controller("SRC001").get_model()
        target_account = self.controller.get_account_controller("TGT001").get_model()
        
        self.assertEqual(source_account.balance, Decimal("800.00"))
        self.assertEqual(target_account.balance, Decimal("700.00"))
        
        # Test transfer with non-existent account
        with self.assertRaises(ValueError):
            self.controller.transfer_between_accounts("SRC001", "NONEXISTENT", Decimal("100.00"))
    
    def test_get_account_summary(self):
        """Test getting account summary"""
        # Add accounts
        self.controller.add_account("Account 1", "ACC001", Decimal("1000.00"))
        self.controller.add_account("Account 2", "ACC002", Decimal("500.00"))
        
        # Get summary
        summary = self.controller.get_account_summary()
        
        # Verify summary
        self.assertEqual(summary['total_accounts'], 2)
        self.assertIn('ACC001', summary['accounts'])
        self.assertIn('ACC002', summary['accounts'])
        self.assertEqual(summary['accounts']['ACC001']['name'], "Account 1")
        self.assertEqual(summary['accounts']['ACC002']['name'], "Account 2")


class TestAgentController(unittest.TestCase):
    """Test AgentController functionality"""
    
    def setUp(self):
        """Setup test environment"""
        AgentImpl.reset_executor()
        self.view = MockView()
        self.account_list_controller = AccountListController()
        self.account_list_controller.set_view(self.view)
        self.controller = AgentController(self.account_list_controller)
        self.controller.set_view(self.view)
        
        # Add test accounts
        self.account_list_controller.add_account("Test 1", "TEST001", Decimal("1000.00"))
        self.account_list_controller.add_account("Test 2", "TEST002", Decimal("1000.00"))
    
    def tearDown(self):
        """Cleanup after tests"""
        self.controller.stop_concurrent_test()
        AgentImpl.shutdown_executor()
    
    def test_agent_controller_creation(self):
        """Test AgentController creation"""
        self.assertIsNone(self.controller.get_model())
        self.assertEqual(self.controller.get_view(), self.view)
        self.assertFalse(self.controller.is_test_running())
    
    def test_start_concurrent_test(self):
        """Test starting concurrent test"""
        # Start test
        self.controller.start_concurrent_test(Decimal("10.00"), Decimal("5.00"), 5)
        
        # Verify test is running
        self.assertTrue(self.controller.is_test_running())
        
        # Verify view was notified
        self.assertIn("test_started_2", self.view.test_events)
        
        # Test starting test when already running
        self.controller.start_concurrent_test(Decimal("10.00"), Decimal("5.00"), 5)
        self.assertIn("Test already running", self.view.errors)
    
    def test_stop_concurrent_test(self):
        """Test stopping concurrent test"""
        # Start test
        self.controller.start_concurrent_test(Decimal("10.00"), Decimal("5.00"), 5)
        
        # Stop test
        self.controller.stop_concurrent_test()
        
        # Verify test is stopped
        self.assertFalse(self.controller.is_test_running())
        
        # Verify view was notified
        self.assertIn("test_stopped", self.view.test_events)
    
    def test_get_test_status(self):
        """Test getting test status"""
        # Get initial status
        status = self.controller.get_test_status()
        self.assertFalse(status['test_running'])
        self.assertEqual(status['total_accounts'], 2)
        self.assertEqual(status['total_agents'], 0)
        self.assertEqual(status['active_agents'], 0)
        
        # Start test and get status
        self.controller.start_concurrent_test(Decimal("10.00"), Decimal("5.00"), 3)
        time.sleep(0.5)  # Let agents start
        
        status = self.controller.get_test_status()
        self.assertTrue(status['test_running'])
        self.assertEqual(status['total_accounts'], 2)
        self.assertGreater(status['total_agents'], 0)
    
    def test_emergency_stop(self):
        """Test emergency stop"""
        # Start test
        self.controller.start_concurrent_test(Decimal("10.00"), Decimal("5.00"), 5)
        
        # Emergency stop
        self.controller.stop_all_operations()
        
        # Verify view was notified
        self.assertIn("emergency_stop", self.view.test_events)


class TestMainController(unittest.TestCase):
    """Test MainController functionality"""
    
    def setUp(self):
        """Setup test environment"""
        AgentImpl.reset_executor()
        self.view = MockView()
        self.controller = MainController()
        self.controller.set_view(self.view)
    
    def tearDown(self):
        """Cleanup after tests"""
        self.controller.shutdown()
    
    def test_main_controller_creation(self):
        """Test MainController creation"""
        self.assertIsNotNone(self.controller.get_account_list_controller())
        self.assertIsNotNone(self.controller.get_agent_controller())
        self.assertEqual(self.controller.get_view(), self.view)
    
    def test_initialize_default_accounts(self):
        """Test initializing default accounts"""
        self.controller.initialize_default_accounts()
        
        # Verify accounts were created
        account_list = self.controller.get_account_list_controller()
        self.assertIsNotNone(account_list.get_account_controller("SAV001"))
        self.assertIsNotNone(account_list.get_account_controller("CHK001"))
        self.assertIsNotNone(account_list.get_account_controller("INV001"))
    
    def test_get_system_status(self):
        """Test getting system status"""
        # Initialize accounts
        self.controller.initialize_default_accounts()
        
        # Get system status
        status = self.controller.get_system_status()
        
        # Verify status structure
        self.assertIn('accounts', status)
        self.assertIn('agent_test', status)
        self.assertIn('thread_pool', status)
        self.assertEqual(status['accounts']['total_accounts'], 3)
        self.assertFalse(status['agent_test']['test_running'])
    
    def test_shutdown(self):
        """Test system shutdown"""
        # Initialize accounts and start test
        self.controller.initialize_default_accounts()
        self.controller.get_agent_controller().start_concurrent_test(Decimal("10.00"), Decimal("5.00"), 3)
        
        # Shutdown system
        self.controller.shutdown()
        
        # Verify view was notified
        self.assertIn("system_shutdown", self.view.test_events)


class TestControllerIntegration(unittest.TestCase):
    """Integration tests for controller system"""
    
    def setUp(self):
        """Setup test environment"""
        AgentImpl.reset_executor()
        self.view = MockView()
        self.controller = MainController()
        self.controller.set_view(self.view)
        self.controller.initialize_default_accounts()
    
    def tearDown(self):
        """Cleanup after tests"""
        self.controller.shutdown()
    
    def test_full_workflow(self):
        """Test complete workflow from account creation to agent operations"""
        account_list = self.controller.get_account_list_controller()
        agent_controller = self.controller.get_agent_controller()
        
        # Add new account
        new_account = account_list.add_account("Workflow Test", "WORK001", Decimal("2000.00"))
        
        # Perform operations
        new_account.deposit(Decimal("500.00"))
        new_account.withdraw(Decimal("100.00"))
        
        # Transfer between accounts
        account_list.transfer_between_accounts("WORK001", "SAV001", Decimal("200.00"))
        
        # Start agents
        new_account.start_deposit_agent(Decimal("10.00"), 3)
        new_account.start_withdraw_agent(Decimal("5.00"), 2)
        
        # Wait for completion
        time.sleep(3.0)
        
        # Verify final state
        self.assertEqual(new_account.get_model().balance, Decimal("2220.00"))  # 2000 + 500 - 100 - 200 + 30 - 10
        
        # Get system status
        status = self.controller.get_system_status()
        self.assertEqual(status['accounts']['total_accounts'], 4)
    
    def test_concurrent_operations(self):
        """Test concurrent operations across multiple accounts"""
        account_list = self.controller.get_account_list_controller()
        
        # Start concurrent test
        self.controller.get_agent_controller().start_concurrent_test(Decimal("5.00"), Decimal("2.00"), 5)
        
        # Wait for completion
        time.sleep(5.0)
        
        # Verify all accounts have been affected
        accounts = account_list.get_all_accounts()
        for account_controller in accounts:
            account = account_controller.get_model()
            # Balance should have changed due to agent operations
            self.assertNotEqual(account.balance, Decimal("1000.00"))  # Initial balance
        
        # Stop test
        self.controller.get_agent_controller().stop_concurrent_test()
        
        # Verify test stopped
        self.assertFalse(self.controller.get_agent_controller().is_test_running())


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2) 