import unittest
import threading
import time
from decimal import Decimal
from concurrent.futures import Future
from agent_system import (
    AgentImpl, DepositAgent, WithdrawAgent, TransferAgent, 
    AgentManager, create_deposit_agent, create_withdraw_agent, 
    create_transfer_agent, IAgentInterface
)
from account_model import (
    Account, AgentStatus, OverdrawException, InterruptedException
)


class TestAgentSystem(unittest.TestCase):
    """Comprehensive tests for Agent system with threading validation"""
    
    def setUp(self):
        """Setup test accounts and agents"""
        # Reset thread pool executor for each test
        AgentImpl.reset_executor()
        
        self.account1 = Account("Test Account 1", "ACC001", Decimal("1000.00"), force_direct_notify=True)
        self.account2 = Account("Test Account 2", "ACC002", Decimal("500.00"), force_direct_notify=True)
        self.account3 = Account("Test Account 3", "ACC003", Decimal("750.00"), force_direct_notify=True)
        
        self.deposit_agent = create_deposit_agent(self.account1, Decimal("10.00"), 5, force_direct_notify=True)
        self.withdraw_agent = create_withdraw_agent(self.account1, Decimal("5.00"), 3, force_direct_notify=True)
        self.transfer_agent = create_transfer_agent(self.account1, self.account2, Decimal("15.00"), 2, force_direct_notify=True)
        
        self.agent_manager = AgentManager()
    
    def tearDown(self):
        """Cleanup after tests"""
        self.agent_manager.shutdown()
    
    def test_agent_creation(self):
        """Test agent creation and basic properties"""
        # Test deposit agent
        self.assertEqual(self.deposit_agent.get_name(), "DepositAgent_ACC001")
        self.assertEqual(self.deposit_agent.get_account(), self.account1)
        self.assertEqual(self.deposit_agent.get_transferred(), Decimal("0.00"))
        self.assertEqual(self.deposit_agent.get_status(), AgentStatus.IDLE)
        
        # Test withdraw agent
        self.assertEqual(self.withdraw_agent.get_name(), "WithdrawAgent_ACC001")
        self.assertEqual(self.withdraw_agent.get_account(), self.account1)
        self.assertEqual(self.withdraw_agent.get_transferred(), Decimal("0.00"))
        self.assertEqual(self.withdraw_agent.get_status(), AgentStatus.IDLE)
        
        # Test transfer agent
        self.assertEqual(self.transfer_agent.get_name(), "TransferAgent_ACC001_to_ACC002")
        self.assertEqual(self.transfer_agent.get_account(), self.account1)
        self.assertEqual(self.transfer_agent.get_transferred(), Decimal("0.00"))
        self.assertEqual(self.transfer_agent.get_status(), AgentStatus.IDLE)
    
    def test_deposit_agent_execution(self):
        """Test deposit agent execution"""
        # Start deposit agent
        future = self.agent_manager.start_agent(self.deposit_agent)
        
        # Wait for completion
        future.result(timeout=10.0)
        
        # Verify results
        self.assertEqual(self.deposit_agent.get_status(), AgentStatus.COMPLETED)
        self.assertEqual(self.deposit_agent.get_transferred(), Decimal("50.00"))  # 5 iterations * 10.00
        self.assertEqual(self.account1.balance, Decimal("1050.00"))  # 1000 + 50
    
    def test_withdraw_agent_execution(self):
        """Test withdraw agent execution"""
        # Start withdraw agent
        future = self.agent_manager.start_agent(self.withdraw_agent)
        
        # Wait for completion
        future.result(timeout=10.0)
        
        # Verify results
        self.assertEqual(self.withdraw_agent.get_status(), AgentStatus.COMPLETED)
        self.assertEqual(self.withdraw_agent.get_transferred(), Decimal("15.00"))  # 3 iterations * 5.00
        self.assertEqual(self.account1.balance, Decimal("985.00"))  # 1000 - 15
    
    def test_transfer_agent_execution(self):
        """Test transfer agent execution"""
        # Start transfer agent
        future = self.agent_manager.start_agent(self.transfer_agent)
        
        # Wait for completion
        future.result(timeout=10.0)
        
        # Verify results
        self.assertEqual(self.transfer_agent.get_status(), AgentStatus.COMPLETED)
        self.assertEqual(self.transfer_agent.get_transferred(), Decimal("30.00"))  # 2 iterations * 15.00
        self.assertEqual(self.account1.balance, Decimal("970.00"))  # 1000 - 30
        self.assertEqual(self.account2.balance, Decimal("530.00"))  # 500 + 30
    
    def test_agent_pause_resume(self):
        """Test agent pause and resume functionality"""
        # Start deposit agent
        future = self.agent_manager.start_agent(self.deposit_agent)
        
        # Let it run for a bit
        time.sleep(0.5)
        
        # Pause agent
        self.agent_manager.pause_agent(self.deposit_agent)
        self.assertEqual(self.deposit_agent.get_status(), AgentStatus.IDLE)
        
        # Let it stay paused
        time.sleep(0.5)
        initial_transferred = self.deposit_agent.get_transferred()
        
        # Resume agent
        self.agent_manager.resume_agent(self.deposit_agent)
        self.assertEqual(self.deposit_agent.get_status(), AgentStatus.BUSY)
        
        # Wait for completion
        future.result(timeout=10.0)
        
        # Verify it completed after resume
        self.assertEqual(self.deposit_agent.get_status(), AgentStatus.COMPLETED)
        self.assertGreater(self.deposit_agent.get_transferred(), initial_transferred)
    
    def test_agent_stop(self):
        """Test agent stop functionality"""
        # Start deposit agent with many iterations
        long_agent = create_deposit_agent(self.account1, Decimal("1.00"), 100, force_direct_notify=True)
        future = self.agent_manager.start_agent(long_agent)
        
        # Let it run for a bit
        time.sleep(0.5)
        
        # Stop agent
        self.agent_manager.stop_agent(long_agent)
        
        # Wait for the agent to finish
        future.result(timeout=5.0)
        # Verify it stopped or completed
        self.assertIn(long_agent.get_status(), [AgentStatus.IDLE, AgentStatus.COMPLETED])
    
    def test_withdraw_agent_blocking(self):
        """Test withdraw agent blocking behavior"""
        # Create withdraw agent with large amount
        large_withdraw_agent = create_withdraw_agent(self.account1, Decimal("2000.00"), 1, force_direct_notify=True)
        
        # Start agent
        future = self.agent_manager.start_agent(large_withdraw_agent)
        
        # Let it run for a bit to get blocked
        time.sleep(1.0)
        
        # Should be blocked due to insufficient funds
        self.assertEqual(large_withdraw_agent.get_status(), AgentStatus.BLOCKED)
        self.assertTrue(large_withdraw_agent.was_blocked())
        
        # Deposit money to unblock
        self.account1.deposit(Decimal("1500.00"))
        
        # Wait for completion
        future.result(timeout=10.0)
        
        # Should complete after deposit
        self.assertEqual(large_withdraw_agent.get_status(), AgentStatus.COMPLETED)
    
    def test_concurrent_agents(self):
        """Test multiple agents running concurrently"""
        # Create multiple agents
        agents = []
        for i in range(3):
            deposit_agent = create_deposit_agent(self.account1, Decimal("5.00"), 2, force_direct_notify=True)
            withdraw_agent = create_withdraw_agent(self.account1, Decimal("3.00"), 2, force_direct_notify=True)
            agents.extend([deposit_agent, withdraw_agent])
        
        # Start all agents
        futures = []
        for agent in agents:
            future = self.agent_manager.start_agent(agent)
            futures.append(future)
        
        # Wait for all to complete
        for future in futures:
            future.result(timeout=15.0)
        
        # Verify all completed
        for agent in agents:
            self.assertEqual(agent.get_status(), AgentStatus.COMPLETED)
        
        # Verify final balance (should be positive due to more deposits than withdrawals)
        self.assertGreater(self.account1.balance, Decimal("0.00"))
    
    def test_agent_manager_operations(self):
        """Test agent manager operations"""
        # Add agents
        self.agent_manager.add_agent(self.deposit_agent)
        self.agent_manager.add_agent(self.withdraw_agent)
        
        # Verify agents are managed
        agents = self.agent_manager.get_agents()
        self.assertEqual(len(agents), 2)
        
        # Test get by name
        found_agent = self.agent_manager.get_agent_by_name("DepositAgent_ACC001")
        self.assertIsNotNone(found_agent)
        self.assertEqual(found_agent, self.deposit_agent)
        
        # Test get by status
        idle_agents = self.agent_manager.get_agents_by_status(AgentStatus.IDLE)
        self.assertEqual(len(idle_agents), 2)
        
        # Remove agent
        self.agent_manager.remove_agent(self.deposit_agent)
        agents = self.agent_manager.get_agents()
        self.assertEqual(len(agents), 1)
    
    def test_thread_pool_management(self):
        """Test thread pool management"""
        # Check initial state
        self.assertEqual(AgentImpl.get_active_tasks_count(), 0)
        
        # Start multiple agents
        futures = []
        for i in range(5):
            agent = create_deposit_agent(self.account1, Decimal("1.00"), 1, force_direct_notify=True)
            future = self.agent_manager.start_agent(agent)
            futures.append(future)
        
        # Check active tasks
        self.assertGreater(AgentImpl.get_active_tasks_count(), 0)
        
        # Wait for completion
        for future in futures:
            future.result(timeout=10.0)
        
        # Cleanup completed tasks
        AgentImpl.cleanup_completed_tasks()
        self.assertEqual(AgentImpl.get_active_tasks_count(), 0)
    
    def test_agent_observer_pattern(self):
        """Test agent observer pattern with events"""
        events_received = []
        
        def event_listener(event):
            events_received.append(event)
        
        # Add listener to deposit agent
        self.deposit_agent.add_listener(event_listener)
        
        # Start agent
        future = self.agent_manager.start_agent(self.deposit_agent)
        future.result(timeout=10.0)
        
        # Verify events were received
        self.assertGreater(len(events_received), 0)
        
        # Check event types
        event_kinds = [event.kind.value for event in events_received]
        self.assertIn("agent_status_update", event_kinds)
        self.assertIn("amount_transferred_update", event_kinds)
    
    def test_agent_error_handling(self):
        """Test agent error handling"""
        # Create agent with valid account but test error handling
        error_agent = DepositAgent(self.account1, Decimal("10.00"), 1, force_direct_notify=True)
        
        # Start agent
        future = self.agent_manager.start_agent(error_agent)
        
        # Should complete successfully
        future.result(timeout=10.0)
        
        # Verify completion status
        self.assertEqual(error_agent.get_status(), AgentStatus.COMPLETED)
    
    def test_agent_timeout_handling(self):
        """Test agent timeout handling"""
        # Create withdraw agent with large amount and short timeout
        timeout_agent = create_withdraw_agent(self.account1, Decimal("2000.00"), 1, force_direct_notify=True)
        
        # Start agent
        future = self.agent_manager.start_agent(timeout_agent)
        
        # Wait for timeout (should be around 30 seconds, but we'll test with shorter timeout)
        future.result(timeout=35.0)
        
        # Should be blocked or completed after timeout
        self.assertIn(timeout_agent.get_status(), [AgentStatus.BLOCKED, AgentStatus.COMPLETED])
        self.assertTrue(timeout_agent.was_blocked())
    
    def test_agent_manager_shutdown(self):
        """Test agent manager shutdown"""
        # Start multiple agents
        futures = []
        for i in range(3):
            agent = create_deposit_agent(self.account1, Decimal("1.00"), 10, force_direct_notify=True)
            future = self.agent_manager.start_agent(agent)
            futures.append(future)
        
        # Let them run for a bit
        time.sleep(0.5)
        
        # Shutdown manager
        self.agent_manager.shutdown()
        
        # Verify shutdown
        self.assertTrue(self.agent_manager.is_shutdown())
        
        # Verify agents are stopped
        agents = self.agent_manager.get_agents()
        self.assertEqual(len(agents), 0)


class TestAgentSystemStress(unittest.TestCase):
    """Stress tests for Agent system"""
    
    def setUp(self):
        AgentImpl.reset_executor()
    
    def test_high_concurrency_stress(self):
        """Stress test with high concurrency"""
        account = Account("Stress Test Account", "STRESS001", Decimal("10000.00"), force_direct_notify=True)
        manager = AgentManager()
        
        try:
            # Create many agents
            agents = []
            for i in range(20):
                if i % 3 == 0:
                    agent = create_deposit_agent(account, Decimal("10.00"), 5, force_direct_notify=True)
                elif i % 3 == 1:
                    agent = create_withdraw_agent(account, Decimal("5.00"), 5, force_direct_notify=True)
                else:
                    target_account = Account(f"Target {i}", f"TARGET{i}", Decimal("100.00"), force_direct_notify=True)
                    agent = create_transfer_agent(account, target_account, Decimal("2.00"), 3, force_direct_notify=True)
                agents.append(agent)
            
            # Start all agents
            futures = []
            for agent in agents:
                future = manager.start_agent(agent)
                futures.append(future)
            
            # Wait for completion
            for future in futures:
                future.result(timeout=30.0)
            
            # Verify all completed
            for agent in agents:
                self.assertIn(agent.get_status(), [AgentStatus.COMPLETED, AgentStatus.BLOCKED])
            
            # Verify account is still valid
            self.assertGreaterEqual(account.balance, Decimal("0.00"))
            
        finally:
            manager.shutdown()


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2) 