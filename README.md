# Python Account Management System

A comprehensive, thread-safe Python implementation of a financial account management system with deadlock prevention, precise decimal arithmetic, and GUI integration.

## 🚀 Critical Features

### ✅ Thread Safety
- **RLock-based synchronization** for all account operations
- **Reentrant locks** prevent deadlocks in nested operations
- **Thread-safe observer pattern** with proper event dispatching

### ✅ Deadlock Prevention
- **Ordered locking strategy** in transfer operations
- **Consistent lock acquisition** based on account ID ordering
- **Comprehensive testing** for concurrent scenarios

### ✅ Precise Decimal Arithmetic
- **28-digit precision** for financial calculations
- **ROUND_HALF_EVEN** rounding for accurate results
- **No floating-point errors** in monetary operations

### ✅ Observer Pattern Integration
- **Thread-safe event notifications** using tkinter.after
- **GUI integration** with real-time updates
- **Multiple event types** for different operations

### ✅ Agent-Based Operations
- **Blocking withdrawals** with timeout handling
- **Agent status tracking** (IDLE, BUSY, BLOCKED, COMPLETED)
- **InterruptedException handling** for interrupted operations

## 📁 Project Structure

```
acctManagerPy2/
├── account_model.py          # Core Account model implementation
├── test_account_model.py     # Comprehensive test suite
├── demo_account_system.py    # GUI demonstration application
├── requirements.txt          # Dependencies (none required)
└── README.md                # This file
```

## 🏗️ Architecture

### Core Classes

#### `AbstractModel` (Base Class)
- Thread-safe observer pattern implementation
- Event dispatching using tkinter.after
- Listener management with proper synchronization

#### `Account` (Main Class)
- Inherits from `AbstractModel`
- Thread-safe financial operations
- Deadlock-free transfer operations
- Transaction history tracking

#### `IAgent` (Agent Interface)
- Thread-safe status management
- Agent lifecycle tracking
- Integration with blocking operations

### Exception Classes
- `OverdrawException`: Insufficient funds handling
- `InterruptedException`: Operation interruption handling

### Event System
- `EventKind`: Enumeration of event types
- `ModelEvent`: Event objects for observer pattern
- `AgentStatus`: Agent state enumeration

## 🧪 Testing

### Running Tests
```bash
# Run all tests with verbose output
python test_account_model.py

# Run specific test class
python -m unittest test_account_model.TestAccountModel -v

# Run stress tests
python -m unittest test_account_model.TestAccountModelStress -v
```

### Test Coverage
- ✅ Basic deposit/withdrawal operations
- ✅ Transfer operations with deadlock prevention
- ✅ Concurrent operations (deposits, withdrawals, transfers)
- ✅ Auto-withdraw with agent status updates
- ✅ Decimal precision validation
- ✅ Observer pattern functionality
- ✅ Thread safety validation
- ✅ Stress testing with high concurrency
- ✅ Exception handling under load

## 🖥️ GUI Demonstration

### Running the Demo
```bash
python demo_account_system.py
```

### Demo Features
- **Real-time account operations** with GUI updates
- **Multiple accounts** with concurrent operations
- **Agent-based auto-withdrawals** with status tracking
- **Event logging** with timestamps
- **Stress testing** with concurrent operations
- **Background operations** simulation

## 💻 Usage Examples

### Basic Account Operations
```python
from decimal import Decimal
from account_model import Account, IAgent

# Create account
account = Account("My Account", "ACC001", Decimal("1000.00"))

# Basic operations
account.deposit(Decimal("100.50"))
account.withdraw(Decimal("25.75"))

# Check balance
print(f"Balance: ${account.balance}")
```

### Transfer Operations
```python
# Create multiple accounts
account1 = Account("Account 1", "ACC001", Decimal("1000.00"))
account2 = Account("Account 2", "ACC002", Decimal("500.00"))

# Transfer (deadlock-free)
account1.transfer(account2, Decimal("100.00"))
```

### Agent-Based Operations
```python
# Create agent
agent = IAgent("Trading Agent")

# Auto-withdraw (blocking operation)
try:
    account.auto_withdraw(Decimal("200.00"), agent)
except InterruptedException:
    print("Operation was interrupted")
```

### Observer Pattern
```python
def event_listener(event):
    print(f"Event: {event.kind.value}, Balance: ${event.balance}")

# Add listener
account.add_listener(event_listener)

# Operations will trigger events
account.deposit(Decimal("50.00"))
```

### Thread-Safe Concurrent Operations
```python
import threading
from decimal import Decimal

def deposit_worker(account, amount, count):
    for _ in range(count):
        account.deposit(amount)

# Create multiple threads
threads = []
for _ in range(5):
    thread = threading.Thread(
        target=deposit_worker, 
        args=(account, Decimal("10.00"), 100)
    )
    threads.append(thread)
    thread.start()

# Wait for completion
for thread in threads:
    thread.join()
```

## 🔒 Thread Safety Features

### Lock Strategy
- **RLock**: Reentrant locks for nested operations
- **Condition variables**: For blocking operations
- **Ordered locking**: Prevents deadlocks in transfers

### Deadlock Prevention
```python
def transfer(self, target: 'Account', amount: Decimal) -> None:
    # CRITICAL: Determine lock order to prevent deadlock
    if self._id < target._id:
        first_account, second_account = self, target
    else:
        first_account, second_account = target, self
    
    # MANDATORY: Acquire locks in consistent order
    with first_account._lock:
        with second_account._lock:
            # Perform transfer logic
```

### Event Dispatching
```python
def notify_changed(self, event: ModelEvent) -> None:
    with self._lock:
        listeners = self._listeners.copy()
    
    if self._root:
        # Use tkinter.after for thread-safe GUI updates
        self._root.after(0, self._dispatch_notifications, listeners, event)
```

## 🎯 Key Design Principles

### 1. Thread Safety First
- All public methods are thread-safe
- Proper synchronization with RLock
- No race conditions in concurrent access

### 2. Deadlock Prevention
- Consistent lock ordering
- Timeout mechanisms for blocking operations
- Proper exception handling

### 3. Financial Accuracy
- Decimal arithmetic for precise calculations
- Proper rounding strategies
- No floating-point errors

### 4. Observer Pattern
- Thread-safe event notifications
- GUI integration support
- Extensible event system

### 5. Comprehensive Testing
- Unit tests for all operations
- Concurrent operation testing
- Stress testing for reliability

## 🚨 Error Handling

### Exception Types
- `ValueError`: Invalid input parameters
- `OverdrawException`: Insufficient funds
- `InterruptedException`: Operation interruption
- `RuntimeError`: System-level errors

### Error Recovery
- Automatic agent status reset on exceptions
- Proper cleanup of blocked agents
- Transaction rollback on failures

## 📊 Performance Characteristics

### Thread Safety Overhead
- Minimal lock contention with RLock
- Efficient event dispatching
- Optimized for concurrent access

### Memory Usage
- Efficient transaction history storage
- Minimal memory footprint per account
- Proper cleanup of completed operations

### Scalability
- Supports hundreds of concurrent operations
- Efficient transfer operations between accounts
- Background operation support

## 🔧 Development

### Code Quality
- Type hints throughout
- Comprehensive docstrings
- PEP 8 compliance
- Exception safety

### Testing Strategy
- Unit tests for all methods
- Integration tests for complex scenarios
- Stress tests for reliability
- GUI integration tests

## 📝 License

This project is provided as-is for educational and demonstration purposes. The implementation follows best practices for thread-safe financial systems.

## 🤝 Contributing

When contributing to this project:

1. Maintain thread safety in all operations
2. Add comprehensive tests for new features
3. Follow the existing code style
4. Document all public interfaces
5. Ensure deadlock prevention in new operations

## 📞 Support

For questions or issues:
1. Review the test suite for usage examples
2. Check the demo application for GUI integration
3. Examine the source code for implementation details

---

**Note**: This system is designed for educational purposes and demonstrates advanced Python threading concepts. For production use, additional security, persistence, and validation features would be required. 