from decimal import Decimal, getcontext, ROUND_HALF_EVEN
from threading import RLock, Condition
import threading
import time
from typing import Optional, Any, List, Callable
from abc import ABC, abstractmethod
from enum import Enum
import tkinter as tk
from tkinter import messagebox


class EventKind(Enum):
    BALANCE_UPDATE = "balance_update"
    AGENT_STATUS_UPDATE = "agent_status_update"
    AMOUNT_TRANSFERRED_UPDATE = "amount_transferred_update"


class ModelEvent:
    """CRITICAL: Event object for observer pattern"""
    def __init__(self, kind: EventKind, balance: Decimal, agent_status: 'AgentStatus'):
        self.kind = kind
        self.balance = balance
        self.agent_status = agent_status


class AgentStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    BLOCKED = "blocked"
    COMPLETED = "completed"


class IAgent:
    """Interface for agent operations"""
    def __init__(self, name: str):
        self.name = name
        self.status = AgentStatus.IDLE
        self._lock = RLock()
    
    def set_status(self, status: AgentStatus) -> None:
        """Thread-safe status update"""
        with self._lock:
            self.status = status
    
    def get_status(self) -> AgentStatus:
        """Thread-safe status retrieval"""
        with self._lock:
            return self.status


class OverdrawException(Exception):
    """MANDATORY: Custom exception for insufficient funds"""
    def __init__(self, attempted_balance: Decimal):
        self.attempted_balance = attempted_balance
        super().__init__(f"Insufficient funds. Attempted balance: {attempted_balance}")


class InterruptedException(Exception):
    """Exception for interrupted operations"""
    def __init__(self, message: str = "Operation was interrupted"):
        super().__init__(message)


class AbstractModel(ABC):
    """
    MANDATORY: Thread-safe observer pattern implementation
    """
    def __init__(self, force_direct_notify: bool = False):
        self._listeners: List[Callable] = []
        self._lock = RLock()
        self._root = None
        self._force_direct_notify = force_direct_notify
        self._setup_root()
    
    def _setup_root(self) -> None:
        """Setup tkinter root window for event dispatching"""
        # Only create tkinter root if we're in the main thread and tkinter is available
        if threading.current_thread() is threading.main_thread():
            try:
                self._root = tk.Tk()
                self._root.withdraw()  # Hide the window
            except (tk.TclError, RuntimeError):
                # If tkinter is not available or already initialized, use None
                self._root = None
        else:
            # In non-main threads, don't create tkinter root
            self._root = None
    
    def add_listener(self, listener: Callable) -> None:
        """CRITICAL: Thread-safe listener management"""
        with self._lock:
            if listener not in self._listeners:
                self._listeners.append(listener)
    
    def remove_listener(self, listener: Callable) -> None:
        """CRITICAL: Thread-safe listener removal"""
        with self._lock:
            if listener in self._listeners:
                self._listeners.remove(listener)
    
    def notify_changed(self, event: ModelEvent) -> None:
        """MANDATORY: Thread-safe notification using tkinter.after or direct if forced"""
        with self._lock:
            listeners = self._listeners.copy()
        
        if self._force_direct_notify or not self._root or threading.current_thread() is not threading.main_thread():
            # Direct dispatch for tests or non-GUI environments
            self._dispatch_notifications(listeners, event)
        else:
            # Use tkinter.after for thread-safe GUI updates (only in main thread)
            try:
                self._root.after(0, self._dispatch_notifications, listeners, event)
            except (tk.TclError, RuntimeError):
                # Fallback if tkinter fails
                self._dispatch_notifications(listeners, event)
    
    def _dispatch_notifications(self, listeners: List[Callable], event: ModelEvent) -> None:
        """Dispatch notifications to all listeners"""
        for listener in listeners:
            try:
                listener(event)
            except Exception as e:
                print(f"Error in listener notification: {e}")


class Account(AbstractModel):
    """
    MANDATORY: Thread-safe financial account with deadlock prevention
    """
    def __init__(self, name: str, account_id: str, initial_balance: Decimal, force_direct_notify: bool = False):
        super().__init__(force_direct_notify=force_direct_notify)
        # CRITICAL: Set decimal precision for financial calculations
        getcontext().prec = 28
        getcontext().rounding = ROUND_HALF_EVEN
        
        self._balance = initial_balance.quantize(Decimal('0.01'))
        self._name = name
        self._id = account_id
        self._lock = RLock()  # MANDATORY: Reentrant lock for thread safety
        self._condition = Condition(self._lock)
        self._transactions: List[dict] = []
        self._blocked_agents: List[IAgent] = []
    
    @property
    def name(self) -> str:
        """Thread-safe name access"""
        with self._lock:
            return self._name
    
    @property
    def account_id(self) -> str:
        """Thread-safe ID access"""
        with self._lock:
            return self._id
    
    @property
    def balance(self) -> Decimal:
        """Thread-safe balance access"""
        with self._lock:
            return self._balance
    
    @property
    def transactions(self) -> List[dict]:
        """Thread-safe transaction history access"""
        with self._lock:
            return self._transactions.copy()
    
    def deposit(self, amount: Decimal) -> None:
        """
        CRITICAL: Thread-safe deposit with precise decimal arithmetic
        MANDATORY: Must notify observers using tkinter.after for GUI updates
        """
        if amount <= 0:
            raise ValueError("Deposit amount must be positive")
        
        amount = amount.quantize(Decimal('0.01'))
        
        with self._lock:
            old_balance = self._balance
            self._balance += amount
            self._balance = self._balance.quantize(Decimal('0.01'))
            
            # Record transaction
            transaction = {
                'type': 'deposit',
                'amount': amount,
                'balance_before': old_balance,
                'balance_after': self._balance,
                'timestamp': time.time()
            }
            self._transactions.append(transaction)
            
            # Notify waiting threads that balance has changed
            self._condition.notify_all()
        
        # CRITICAL: Notify observers with balance update
        event = ModelEvent(
            EventKind.BALANCE_UPDATE,
            self._balance,
            AgentStatus.IDLE
        )
        self.notify_changed(event)
    
    def withdraw(self, amount: Decimal) -> None:
        """
        CRITICAL: Thread-safe withdrawal with OverdrawException
        MANDATORY: Must handle insufficient funds properly
        """
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        
        amount = amount.quantize(Decimal('0.01'))
        
        with self._lock:
            old_balance = self._balance
            new_balance = self._balance - amount
            
            if new_balance < 0:
                raise OverdrawException(new_balance)
            
            self._balance = new_balance.quantize(Decimal('0.01'))
            
            # Record transaction
            transaction = {
                'type': 'withdrawal',
                'amount': amount,
                'balance_before': old_balance,
                'balance_after': self._balance,
                'timestamp': time.time()
            }
            self._transactions.append(transaction)
            
            # Notify waiting threads that balance has changed
            self._condition.notify_all()
        
        # CRITICAL: Notify observers with balance update
        event = ModelEvent(
            EventKind.BALANCE_UPDATE,
            self._balance,
            AgentStatus.IDLE
        )
        self.notify_changed(event)
    
    def auto_withdraw(self, amount: Decimal, agent: IAgent) -> None:
        """
        MANDATORY: Blocking withdrawal with timeout and agent status updates
        CRITICAL: Must handle InterruptedException and agent state changes
        """
        if amount <= 0:
            raise ValueError("Withdrawal amount must be positive")
        
        amount = amount.quantize(Decimal('0.01'))
        
        # Update agent status to busy
        agent.set_status(AgentStatus.BUSY)
        
        try:
            with self._lock:
                # Add agent to blocked list
                if agent not in self._blocked_agents:
                    self._blocked_agents.append(agent)
                
                # Update agent status to blocked
                agent.set_status(AgentStatus.BLOCKED)
                
                # Notify agent status change
                event = ModelEvent(
                    EventKind.AGENT_STATUS_UPDATE,
                    self._balance,
                    agent.get_status()
                )
                self.notify_changed(event)
                
                # Wait for sufficient funds with timeout
                timeout = 30.0  # 30 seconds timeout
                start_time = time.time()
                
                while self._balance < amount:
                    if time.time() - start_time > timeout:
                        agent.set_status(AgentStatus.IDLE)
                        if agent in self._blocked_agents:
                            self._blocked_agents.remove(agent)
                        # Notify agent status change on timeout
                        event = ModelEvent(
                            EventKind.AGENT_STATUS_UPDATE,
                            self._balance,
                            agent.get_status()
                        )
                        self.notify_changed(event)
                        raise InterruptedException("Withdrawal timeout - insufficient funds")
                    
                    # Wait for balance change
                    self._condition.wait(timeout=1.0)
                    
                    # Check if thread was interrupted
                    if threading.current_thread().ident != threading.get_ident():
                        agent.set_status(AgentStatus.IDLE)
                        if agent in self._blocked_agents:
                            self._blocked_agents.remove(agent)
                        event = ModelEvent(
                            EventKind.AGENT_STATUS_UPDATE,
                            self._balance,
                            agent.get_status()
                        )
                        self.notify_changed(event)
                        raise InterruptedException("Thread interrupted during withdrawal")
                
                # Notify condition when balance changes
                self._condition.notify_all()
                
                # Perform withdrawal
                old_balance = self._balance
                self._balance -= amount
                self._balance = self._balance.quantize(Decimal('0.01'))
                
                # Record transaction
                transaction = {
                    'type': 'auto_withdrawal',
                    'amount': amount,
                    'balance_before': old_balance,
                    'balance_after': self._balance,
                    'agent': agent.name,
                    'timestamp': time.time()
                }
                self._transactions.append(transaction)
                
                # Update agent status to completed
                agent.set_status(AgentStatus.COMPLETED)
                
                # Remove agent from blocked list
                if agent in self._blocked_agents:
                    self._blocked_agents.remove(agent)
                
                # Notify completion
                event = ModelEvent(
                    EventKind.AGENT_STATUS_UPDATE,
                    self._balance,
                    agent.get_status()
                )
                self.notify_changed(event)
                
        except Exception as e:
            # Ensure agent is removed from blocked list on any exception
            with self._lock:
                if agent in self._blocked_agents:
                    self._blocked_agents.remove(agent)
                agent.set_status(AgentStatus.IDLE)
                # Notify agent status change on exception
                event = ModelEvent(
                    EventKind.AGENT_STATUS_UPDATE,
                    self._balance,
                    agent.get_status()
                )
                self.notify_changed(event)
            raise e
    
    def transfer(self, target: 'Account', amount: Decimal) -> None:
        """
        CRITICAL: Deadlock-free transfer using ordered locking
        MANDATORY: Lock accounts in consistent order based on account_id
        """
        if target is None:
            raise ValueError("Target account cannot be None")
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")
        if self is target:
            raise ValueError("Cannot transfer to same account")
        
        amount = amount.quantize(Decimal('0.01'))
        
        # CRITICAL: Determine lock order to prevent deadlock
        if self._id < target._id:
            first_account, second_account = self, target
        else:
            first_account, second_account = target, self
        
        # MANDATORY: Acquire locks in consistent order
        with first_account._lock:
            with second_account._lock:
                # Check sufficient funds in source account
                if self._balance < amount:
                    raise OverdrawException(self._balance - amount)
                
                # Perform transfer
                self._balance -= amount
                self._balance = self._balance.quantize(Decimal('0.01'))
                
                target._balance += amount
                target._balance = target._balance.quantize(Decimal('0.01'))
                
                # Record transactions
                timestamp = time.time()
                
                # Source account transaction
                source_transaction = {
                    'type': 'transfer_out',
                    'amount': amount,
                    'target_account': target._id,
                    'balance_before': self._balance + amount,
                    'balance_after': self._balance,
                    'timestamp': timestamp
                }
                self._transactions.append(source_transaction)
                
                # Target account transaction
                target_transaction = {
                    'type': 'transfer_in',
                    'amount': amount,
                    'source_account': self._id,
                    'balance_before': target._balance - amount,
                    'balance_after': target._balance,
                    'timestamp': timestamp
                }
                target._transactions.append(target_transaction)
                
                # Notify both accounts
                source_event = ModelEvent(
                    EventKind.AMOUNT_TRANSFERRED_UPDATE,
                    self._balance,
                    AgentStatus.IDLE
                )
                self.notify_changed(source_event)
                
                target_event = ModelEvent(
                    EventKind.AMOUNT_TRANSFERRED_UPDATE,
                    target._balance,
                    AgentStatus.IDLE
                )
                target.notify_changed(target_event)
    
    def get_transaction_summary(self) -> dict:
        """Thread-safe transaction summary"""
        with self._lock:
            total_deposits = sum(
                t['amount'] for t in self._transactions 
                if t['type'] in ['deposit', 'transfer_in']
            )
            total_withdrawals = sum(
                t['amount'] for t in self._transactions 
                if t['type'] in ['withdrawal', 'auto_withdrawal', 'transfer_out']
            )
            
            return {
                'account_id': self._id,
                'name': self._name,
                'current_balance': self._balance,
                'total_deposits': total_deposits,
                'total_withdrawals': total_withdrawals,
                'transaction_count': len(self._transactions),
                'blocked_agents_count': len(self._blocked_agents)
            }
    
    def __str__(self) -> str:
        return f"Account({self._id}: {self._name}, Balance: ${self._balance})"
    
    def __repr__(self) -> str:
        return self.__str__() 