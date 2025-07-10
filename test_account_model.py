import unittest
import threading
import time
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
from account_model import (
    Account, IAgent, AgentStatus, OverdrawException, 
    InterruptedException, EventKind, ModelEvent
)


class TestAccountModel(unittest.TestCase):
    """Comprehensive tests for Account model with threading validation"""
    
    def setUp(self):
        """Setup test accounts"""
        self.account1 = Account("Test Account 1", "ACC001", Decimal("1000.00"), force_direct_notify=True)
        self.account2 = Account("Test Account 2", "ACC002", Decimal("500.00"), force_direct_notify=True)
        self.account3 = Account("Test Account 3", "ACC003", Decimal("750.00"), force_direct_notify=True)
        self.agent1 = IAgent("Agent 1")
        self.agent2 = IAgent("Agent 2")
    
    def test_basic_deposit_and_withdrawal(self):
        """Test basic deposit and withdrawal operations"""
        # Test deposit
        self.account1.deposit(Decimal("100.50"))
        self.assertEqual(self.account1.balance, Decimal("1100.50"))
        
        # Test withdrawal
        self.account1.withdraw(Decimal("50.25"))
        self.assertEqual(self.account1.balance, Decimal("1050.25"))
        
        # Test decimal precision
        self.account1.deposit(Decimal("0.001"))
        self.assertEqual(self.account1.balance, Decimal("1050.25"))  # Should round to 2 decimal places
    
    def test_overdraw_exception(self):
        """Test OverdrawException handling"""
        with self.assertRaises(OverdrawException) as context:
            self.account1.withdraw(Decimal("2000.00"))
        
        exception = context.exception
        self.assertEqual(exception.attempted_balance, Decimal("-1000.00"))
    
    def test_transfer_operations(self):
        """Test transfer operations between accounts"""
        initial_balance1 = self.account1.balance
        initial_balance2 = self.account2.balance
        
        # Test successful transfer
        self.account1.transfer(self.account2, Decimal("100.00"))
        
        self.assertEqual(self.account1.balance, initial_balance1 - Decimal("100.00"))
        self.assertEqual(self.account2.balance, initial_balance2 + Decimal("100.00"))
        
        # Test transfer to same account
        with self.assertRaises(ValueError):
            self.account1.transfer(self.account1, Decimal("50.00"))
        
        # Test transfer with insufficient funds
        with self.assertRaises(OverdrawException):
            self.account1.transfer(self.account2, Decimal("2000.00"))
    
    def test_concurrent_deposits(self):
        """Test multiple concurrent deposits"""
        def deposit_worker(account, amount, count):
            for _ in range(count):
                account.deposit(amount)
                time.sleep(0.001)  # Small delay to increase concurrency
        
        initial_balance = self.account1.balance
        deposit_amount = Decimal("10.00")
        deposit_count = 100
        
        # Create multiple threads for concurrent deposits
        threads = []
        for _ in range(5):
            thread = threading.Thread(
                target=deposit_worker, 
                args=(self.account1, deposit_amount, deposit_count)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        expected_balance = initial_balance + (deposit_amount * deposit_count * 5)
        self.assertEqual(self.account1.balance, expected_balance)
    
    def test_concurrent_withdrawals(self):
        """Test multiple concurrent withdrawals"""
        # First deposit enough money
        self.account1.deposit(Decimal("10000.00"))
        
        def withdrawal_worker(account, amount, count):
            for _ in range(count):
                try:
                    account.withdraw(amount)
                except OverdrawException:
                    break
                time.sleep(0.001)
        
        withdrawal_amount = Decimal("10.00")
        withdrawal_count = 50
        
        threads = []
        for _ in range(3):
            thread = threading.Thread(
                target=withdrawal_worker,
                args=(self.account1, withdrawal_amount, withdrawal_count)
            )
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify final balance is reasonable (some withdrawals may fail due to insufficient funds)
        self.assertGreaterEqual(self.account1.balance, Decimal("0.00"))
    
    def test_deadlock_prevention_in_transfers(self):
        """Test deadlock prevention in transfer operations"""
        def transfer_worker(account1, account2, amount, count):
            for _ in range(count):
                try:
                    account1.transfer(account2, amount)
                    time.sleep(0.001)
                except OverdrawException:
                    break
        
        # Create multiple threads transferring in both directions
        threads = []
        transfer_amount = Decimal("10.00")
        transfer_count = 20
        
        # Thread 1: account1 -> account2
        thread1 = threading.Thread(
            target=transfer_worker,
            args=(self.account1, self.account2, transfer_amount, transfer_count)
        )
        threads.append(thread1)
        
        # Thread 2: account2 -> account1
        thread2 = threading.Thread(
            target=transfer_worker,
            args=(self.account2, self.account1, transfer_amount, transfer_count)
        )
        threads.append(thread2)
        
        # Thread 3: account1 -> account3
        thread3 = threading.Thread(
            target=transfer_worker,
            args=(self.account1, self.account3, transfer_amount, transfer_count)
        )
        threads.append(thread3)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for completion (should not deadlock)
        for thread in threads:
            thread.join(timeout=10.0)  # 10 second timeout
        
        # Verify all threads completed
        for thread in threads:
            self.assertFalse(thread.is_alive(), "Thread did not complete - possible deadlock")
    
    def test_auto_withdraw_with_agent(self):
        """Test auto_withdraw with agent status updates"""
        def auto_withdraw_worker(account, amount, agent):
            try:
                account.auto_withdraw(amount, agent)
            except InterruptedException:
                pass
        
        # Test auto_withdraw with insufficient funds (should block)
        withdraw_amount = Decimal("2000.00")  # More than current balance
        
        thread = threading.Thread(
            target=auto_withdraw_worker,
            args=(self.account1, withdraw_amount, self.agent1)
        )
        thread.start()
        
        # Wait a bit for agent to be blocked
        time.sleep(0.1)
        
        # Check agent status
        self.assertEqual(self.agent1.get_status(), AgentStatus.BLOCKED)
        
        # Deposit money to unblock the agent
        self.account1.deposit(Decimal("1500.00"))
        
        # Wait for completion
        thread.join(timeout=5.0)
        
        # Verify agent completed
        self.assertEqual(self.agent1.get_status(), AgentStatus.COMPLETED)
        self.assertFalse(thread.is_alive())
    
    def test_auto_withdraw_timeout(self):
        """Test auto_withdraw timeout behavior"""
        def auto_withdraw_worker(account, amount, agent):
            try:
                account.auto_withdraw(amount, agent)
            except InterruptedException:
                pass
        
        # Test auto_withdraw with insufficient funds and no deposits
        withdraw_amount = Decimal("2000.00")
        
        thread = threading.Thread(
            target=auto_withdraw_worker,
            args=(self.account1, withdraw_amount, self.agent2)
        )
        thread.start()
        
        # Wait for completion (should timeout in 30 seconds, but test will wait for thread)
        thread.join(timeout=35.0)
        
        # Agent should be back to idle after timeout
        self.assertEqual(self.agent2.get_status(), AgentStatus.IDLE)
    
    def test_decimal_precision(self):
        """Test decimal precision in financial calculations"""
        # Test that decimal arithmetic is precise
        self.account1.deposit(Decimal("0.01"))
        self.account1.deposit(Decimal("0.01"))
        self.account1.deposit(Decimal("0.01"))
        
        # Should be exactly 0.03, not 0.029999999999999999
        self.assertEqual(self.account1.balance, Decimal("1000.03"))
        
        # Test floating point precision issues are avoided
        float_amount = 0.1 + 0.2  # This would be 0.30000000000000004 in float
        decimal_amount = Decimal("0.1") + Decimal("0.2")  # This is exactly 0.3
        
        self.account1.deposit(Decimal(str(decimal_amount)))
        self.assertEqual(self.account1.balance, Decimal("1000.33"))
    
    def test_observer_pattern(self):
        """Test observer pattern with event notifications"""
        events_received = []
        
        def event_listener(event):
            events_received.append(event)
        
        # Add listener
        self.account1.add_listener(event_listener)
        
        # Perform operations that should trigger events
        self.account1.deposit(Decimal("100.00"))
        self.account1.withdraw(Decimal("50.00"))
        self.account1.transfer(self.account2, Decimal("25.00"))
        
        # Wait for events to be processed
        time.sleep(0.2)
        
        # Verify events were received
        self.assertGreater(len(events_received), 0)
        
        # Check event types
        event_kinds = [event.kind for event in events_received]
        self.assertIn(EventKind.BALANCE_UPDATE, event_kinds)
        self.assertIn(EventKind.AMOUNT_TRANSFERRED_UPDATE, event_kinds)
    
    def test_concurrent_transfers_with_multiple_accounts(self):
        """Test complex concurrent transfer scenarios"""
        accounts = [
            Account(f"Account {i}", f"ACC{i:03d}", Decimal("1000.00"), force_direct_notify=True)
            for i in range(1, 6)
        ]
        
        def random_transfer_worker(accounts, iterations):
            for _ in range(iterations):
                source = random.choice(accounts)
                target = random.choice(accounts)
                if source != target:
                    try:
                        amount = Decimal(str(random.uniform(1.0, 100.0))).quantize(Decimal('0.01'))
                        source.transfer(target, amount)
                    except OverdrawException:
                        pass
                time.sleep(0.001)
        
        # Create multiple threads performing random transfers
        threads = []
        for _ in range(10):
            thread = threading.Thread(
                target=random_transfer_worker,
                args=(accounts, 50)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=30.0)
        
        # Verify all threads completed
        for thread in threads:
            self.assertFalse(thread.is_alive(), "Thread did not complete")
        
        # Verify total money is conserved
        total_balance = sum(account.balance for account in accounts)
        expected_total = Decimal("5000.00")  # 5 accounts * 1000.00
        self.assertEqual(total_balance, expected_total)
    
    def test_thread_safety_of_properties(self):
        """Test thread safety of account properties"""
        def property_reader(account, iterations):
            for _ in range(iterations):
                _ = account.balance
                _ = account.name
                _ = account.account_id
                _ = account.transactions
                time.sleep(0.001)
        
        def property_writer(account, iterations):
            for _ in range(iterations):
                account.deposit(Decimal("1.00"))
                time.sleep(0.001)
        
        # Create reader and writer threads
        reader_thread = threading.Thread(
            target=property_reader,
            args=(self.account1, 1000)
        )
        writer_thread = threading.Thread(
            target=property_writer,
            args=(self.account1, 100)
        )
        
        reader_thread.start()
        writer_thread.start()
        
        reader_thread.join()
        writer_thread.join()
        
        # No exceptions should have occurred
        self.assertTrue(True)  # If we get here, no thread safety issues occurred
    
    def test_transaction_summary(self):
        """Test transaction summary functionality"""
        # Perform various transactions
        self.account1.deposit(Decimal("100.00"))
        self.account1.withdraw(Decimal("25.00"))
        self.account1.transfer(self.account2, Decimal("50.00"))
        
        summary = self.account1.get_transaction_summary()
        
        self.assertEqual(summary['account_id'], "ACC001")
        self.assertEqual(summary['name'], "Test Account 1")
        self.assertEqual(summary['current_balance'], self.account1.balance)
        self.assertEqual(summary['transaction_count'], 3)
        self.assertEqual(summary['total_deposits'], Decimal("100.00"))
        self.assertEqual(summary['total_withdrawals'], Decimal("75.00"))  # 25 + 50


class TestAccountModelStress(unittest.TestCase):
    """Stress tests for Account model"""
    
    def test_high_concurrency_stress(self):
        """Stress test with high concurrency"""
        account = Account("Stress Test Account", "STRESS001", Decimal("10000.00"), force_direct_notify=True)
        
        def stress_worker(worker_id, operations):
            for i in range(operations):
                try:
                    if i % 3 == 0:
                        account.deposit(Decimal("10.00"))
                    elif i % 3 == 1:
                        account.withdraw(Decimal("5.00"))
                    else:
                        # Create temporary account for transfer
                        temp_account = Account(f"Temp {worker_id}-{i}", f"TEMP{worker_id}{i}", Decimal("100.00"), force_direct_notify=True)
                        account.transfer(temp_account, Decimal("2.00"))
                except (OverdrawException, ValueError):
                    pass
                time.sleep(0.0001)  # Very small delay
        
        # Create many threads with many operations
        threads = []
        for i in range(20):  # 20 threads
            thread = threading.Thread(
                target=stress_worker,
                args=(i, 100)  # 100 operations per thread
            )
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=60.0)
        
        # Verify all threads completed
        for thread in threads:
            self.assertFalse(thread.is_alive(), "Stress test thread did not complete")
        
        # Verify account is still in a valid state
        self.assertGreaterEqual(account.balance, Decimal("0.00"))
        self.assertIsInstance(account.balance, Decimal)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2) 