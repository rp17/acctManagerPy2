from abc import ABC, abstractmethod
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, Future
from threading import RLock, Condition, Event
import threading
import time
import multiprocessing
from typing import Optional, Any, List
from enum import Enum
from model.account_model import (
    Account, AbstractModel, ModelEvent, EventKind, 
    OverdrawException, InterruptedException, AgentStatus, IAgent
)


class IAgentInterface(ABC):
    """
    MANDATORY: Agent interface with threading and financial operations
    """
    @abstractmethod
    def get_transferred(self) -> Decimal:
        """CRITICAL: Return total amount transferred"""
        pass
    
    @abstractmethod
    def on_pause(self) -> None:
        """MANDATORY: Handle pause signal"""
        pass
    
    @abstractmethod
    def on_resume(self) -> None:
        """MANDATORY: Handle resume signal"""
        pass
    
    @abstractmethod
    def set_status(self, status: AgentStatus) -> None:
        """CRITICAL: Thread-safe status updates"""
        pass
    
    @abstractmethod
    def get_account(self) -> 'Account':
        """MANDATORY: Return associated account"""
        pass
    
    @abstractmethod
    def run(self) -> None:
        """CRITICAL: Main agent execution loop"""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """MANDATORY: Stop agent execution"""
        pass
    
    @abstractmethod
    def get_status(self) -> AgentStatus:
        """MANDATORY: Get current agent status"""
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """MANDATORY: Get agent name"""
        pass


class AgentImpl(AbstractModel, IAgentInterface):
    """
    CRITICAL: Base implementation for all agents with thread management
    """
    # MANDATORY: Class-level thread pool
    _cpu_count = multiprocessing.cpu_count()
    _executor = ThreadPoolExecutor(max_workers=2 * _cpu_count)
    _active_tasks: List[Future] = []
    _tasks_lock = RLock()
    
    def __init__(self, account: 'Account', amount: Decimal, iterations: int = -1, force_direct_notify: bool = False):
        super().__init__(force_direct_notify=force_direct_notify)
        self._account = account
        self._amount = amount.quantize(Decimal('0.01'))
        self._transferred = Decimal('0.00')
        self._iterations = iterations
        self._status = AgentStatus.IDLE
        self._active = True
        self._paused = False
        self._was_blocked = False
        self._delay = 0.3  # 300ms delay
        self._name = "DefaultAgent"
        
        # CRITICAL: Thread synchronization objects
        self._pause_lock = RLock()
        self._pause_condition = Condition(self._pause_lock)
        self._task_future: Optional[Future] = None
        self._status_lock = RLock()
    
    def get_transferred(self) -> Decimal:
        """CRITICAL: Return total amount transferred"""
        with self._status_lock:
            return self._transferred
    
    def on_pause(self) -> None:
        """MANDATORY: Handle pause signal"""
        with self._pause_lock:
            self._paused = True
            self.set_status(AgentStatus.IDLE)  # Use IDLE for paused state
    
    def on_resume(self) -> None:
        """MANDATORY: Handle resume signal"""
        with self._pause_lock:
            self._paused = False
            self.set_status(AgentStatus.BUSY)  # Use BUSY for running state
            self._pause_condition.notify_all()
    
    def set_status(self, status: AgentStatus) -> None:
        """
        CRITICAL: Thread-safe status updates with event notification
        """
        with self._status_lock:
            self._status = status
            if status == AgentStatus.BLOCKED:
                self._was_blocked = True
            elif status == AgentStatus.BUSY:
                self._was_blocked = False
        
        # MANDATORY: Notify observers using tkinter.after or direct notification
        event = ModelEvent(
            EventKind.AGENT_STATUS_UPDATE,
            self._transferred,
            status
        )
        self.notify_changed(event)
    
    def get_account(self) -> 'Account':
        """MANDATORY: Return associated account"""
        return self._account
    
    def stop(self) -> None:
        """MANDATORY: Stop agent execution"""
        with self._pause_lock:
            self._active = False
            self._pause_condition.notify_all()
        
        # Cancel task if running
        if self._task_future and not self._task_future.done():
            self._task_future.cancel()
    
    def get_status(self) -> AgentStatus:
        """MANDATORY: Get current agent status"""
        with self._status_lock:
            return self._status
    
    def was_blocked(self) -> bool:
        """Check if agent was ever blocked"""
        return self._was_blocked
    
    def get_name(self) -> str:
        """Get agent name"""
        return self._name
    
    @classmethod
    def execute_agent(cls, agent: IAgentInterface) -> Future:
        """
        CRITICAL: Submit agent to thread pool and track execution
        """
        with cls._tasks_lock:
            future = cls._executor.submit(agent.run)
            cls._active_tasks.append(future)
            return future
    
    @classmethod
    def shutdown_executor(cls) -> None:
        """
        MANDATORY: Graceful shutdown of thread pool
        """
        # Cancel all pending tasks
        with cls._tasks_lock:
            for task in cls._active_tasks:
                if not task.done():
                    task.cancel()
            cls._active_tasks.clear()
        
        # Shutdown executor
        cls._executor.shutdown(wait=True)
    
    @classmethod
    def reset_executor(cls) -> None:
        """
        Reset thread pool executor for testing
        """
        # Create new executor
        cls._executor = ThreadPoolExecutor(max_workers=2 * cls._cpu_count)
        cls._active_tasks.clear()
    
    @classmethod
    def get_active_tasks_count(cls) -> int:
        """Get count of active tasks"""
        with cls._tasks_lock:
            return len([task for task in cls._active_tasks if not task.done()])
    
    @classmethod
    def cleanup_completed_tasks(cls) -> None:
        """Remove completed tasks from active list"""
        with cls._tasks_lock:
            cls._active_tasks = [task for task in cls._active_tasks if not task.done()]

    @staticmethod
    def shutdown_and_await_termination():
        """
        MANDATORY: Graceful shutdown of thread pool and await termination
        """
        AgentImpl.shutdown_executor()
        # No explicit await for ThreadPoolExecutor's shutdown, as it's blocking

    @staticmethod
    def create_agent(account: 'Account', agent_type: type, amount: Decimal, iterations: int = -1, 
                     force_direct_notify: bool = False) -> IAgentInterface:
        """
        Convenience method to create agents of a specific type.
        """
        if agent_type == DepositAgent:
            return create_deposit_agent(account, amount, iterations, force_direct_notify)
        elif agent_type == WithdrawAgent:
            return create_withdraw_agent(account, amount, iterations, force_direct_notify)
        elif agent_type == TransferAgent:
            # For TransferAgent, we need a source and target account.
            # This is a placeholder. In a real scenario, you'd get them from somewhere.
            # For now, let's assume a dummy target account or raise an error.
            # A more robust solution would involve a dedicated AccountManager.
            raise ValueError("Source and target accounts must be provided for TransferAgent")
        else:
            raise ValueError(f"Unknown agent type: {agent_type.__name__}")


class DepositAgent(AgentImpl):
    """
    MANDATORY: Thread-safe deposit operations agent
    """
    def __init__(self, account: 'Account', amount: Decimal, iterations: int = -1, force_direct_notify: bool = False):
        super().__init__(account, amount, iterations, force_direct_notify)
        self._name = f"DepositAgent_{account.account_id}"
    
    def run(self) -> None:
        """
        CRITICAL: Main deposit loop with pause/resume handling
        MANDATORY: Must handle InterruptedException and proper cleanup
        """
        try:
            self.set_status(AgentStatus.BUSY)
            
            while self._active and (self._iterations == -1 or self._iterations > 0):
                # CRITICAL: Check for pause condition
                with self._pause_condition:
                    while self._paused and self._active:
                        self._pause_condition.wait()
                
                if not self._active:
                    break
                
                # MANDATORY: Perform deposit operation
                self._account.deposit(self._amount)
                self._transferred += self._amount
                
                if self._iterations > 0:
                    self._iterations -= 1
                
                # CRITICAL: Notify observers of transfer update
                event = ModelEvent(
                    EventKind.AMOUNT_TRANSFERRED_UPDATE,
                    self._transferred,
                    AgentStatus.BUSY
                )
                self.notify_changed(event)
                
                # MANDATORY: Sleep with interruption handling
                time.sleep(self._delay)
                
        except Exception as e:
            self.set_status(AgentStatus.IDLE)  # Use IDLE for error state
            raise
        finally:
            self.set_status(AgentStatus.COMPLETED)  # Use COMPLETED for finished state


class WithdrawAgent(AgentImpl, IAgent):
    """
    MANDATORY: Thread-safe withdrawal operations with blocking support
    """
    def __init__(self, account: 'Account', amount: Decimal, iterations: int = -1, force_direct_notify: bool = False):
        super().__init__(account, amount, iterations, force_direct_notify)
        self._name = f"WithdrawAgent_{account.account_id}"
        # Initialize IAgent interface
        IAgent.__init__(self, self._name)
    
    def run(self) -> None:
        """
        CRITICAL: Main withdrawal loop with auto-withdraw and blocking
        MANDATORY: Must handle insufficient funds and agent blocking
        """
        try:
            self.set_status(AgentStatus.BUSY)
            
            while self._active and (self._iterations == -1 or self._iterations > 0):
                # CRITICAL: Check for pause condition
                with self._pause_condition:
                    while self._paused and self._active:
                        self._pause_condition.wait()
                
                if not self._active:
                    break
                
                try:
                    # MANDATORY: Use auto_withdraw for blocking behavior
                    self._account.auto_withdraw(self._amount, self)
                    self._transferred += self._amount
                    
                    if self._iterations > 0:
                        self._iterations -= 1
                    
                    # CRITICAL: Notify observers
                    event = ModelEvent(
                        EventKind.AMOUNT_TRANSFERRED_UPDATE,
                        self._transferred,
                        AgentStatus.BUSY
                    )
                    self.notify_changed(event)
                    
                except InterruptedException:
                    # MANDATORY: Handle timeout gracefully
                    self.set_status(AgentStatus.BLOCKED)
                    break
                
                # MANDATORY: Sleep with interruption handling
                time.sleep(self._delay)
                
        except Exception as e:
            self.set_status(AgentStatus.IDLE)  # Use IDLE for error state
            raise
        finally:
            self.set_status(AgentStatus.COMPLETED)  # Use COMPLETED for finished state


class TransferAgent(AgentImpl):
    """
    MANDATORY: Thread-safe transfer operations between accounts
    """
    def __init__(self, source_account: 'Account', target_account: 'Account', 
                 amount: Decimal, iterations: int = -1, force_direct_notify: bool = False):
        super().__init__(source_account, amount, iterations, force_direct_notify)
        self._target_account = target_account
        self._name = f"TransferAgent_{source_account.account_id}_to_{target_account.account_id}"
    
    def run(self) -> None:
        """
        CRITICAL: Main transfer loop with deadlock prevention
        MANDATORY: Must handle transfer failures and proper cleanup
        """
        try:
            self.set_status(AgentStatus.BUSY)
            
            while self._active and (self._iterations == -1 or self._iterations > 0):
                # CRITICAL: Check for pause condition
                with self._pause_condition:
                    while self._paused and self._active:
                        self._pause_condition.wait()
                
                if not self._active:
                    break
                
                try:
                    # MANDATORY: Perform transfer with deadlock prevention
                    self._account.transfer(self._target_account, self._amount)
                    self._transferred += self._amount
                    
                    if self._iterations > 0:
                        self._iterations -= 1
                    
                    # CRITICAL: Notify observers
                    event = ModelEvent(
                        EventKind.AMOUNT_TRANSFERRED_UPDATE,
                        self._transferred,
                        AgentStatus.BUSY
                    )
                    self.notify_changed(event)
                    
                except OverdrawException:
                    # MANDATORY: Handle insufficient funds
                    self.set_status(AgentStatus.BLOCKED)
                    break
                except Exception as e:
                    # Handle other transfer errors
                    self.set_status(AgentStatus.IDLE)  # Use IDLE for error state
                    raise
                
                # MANDATORY: Sleep with interruption handling
                time.sleep(self._delay)
                
        except Exception as e:
            self.set_status(AgentStatus.IDLE)  # Use IDLE for error state
            raise
        finally:
            self.set_status(AgentStatus.COMPLETED)  # Use COMPLETED for finished state


class AgentManager:
    """
    MANDATORY: Centralized agent management with thread pool coordination
    """
    def __init__(self):
        self._agents: List[IAgentInterface] = []
        self._agent_lock = RLock()
        self._shutdown_event = Event()
    
    def add_agent(self, agent: IAgentInterface) -> None:
        """Add agent to management"""
        with self._agent_lock:
            self._agents.append(agent)
    
    def remove_agent(self, agent: IAgentInterface) -> None:
        """Remove agent from management"""
        with self._agent_lock:
            if agent in self._agents:
                self._agents.remove(agent)
    
    def start_agent(self, agent: IAgentInterface) -> Future:
        """Start agent execution"""
        self.add_agent(agent)
        return AgentImpl.execute_agent(agent)
    
    def stop_agent(self, agent: IAgentInterface) -> None:
        """Stop specific agent"""
        agent.stop()
        self.remove_agent(agent)
    
    def pause_agent(self, agent: IAgentInterface) -> None:
        """Pause specific agent"""
        agent.on_pause()
    
    def resume_agent(self, agent: IAgentInterface) -> None:
        """Resume specific agent"""
        agent.on_resume()
    
    def pause_all_agents(self) -> None:
        """Pause all managed agents"""
        with self._agent_lock:
            for agent in self._agents:
                agent.on_pause()
    
    def resume_all_agents(self) -> None:
        """Resume all managed agents"""
        with self._agent_lock:
            for agent in self._agents:
                agent.on_resume()
    
    def stop_all_agents(self) -> None:
        """Stop all managed agents"""
        with self._agent_lock:
            for agent in self._agents:
                agent.stop()
            self._agents.clear()
    
    def get_agents(self) -> List[IAgentInterface]:
        """Get all managed agents"""
        with self._agent_lock:
            return self._agents.copy()
    
    def get_agent_by_name(self, name: str) -> Optional[IAgentInterface]:
        """Get agent by name"""
        with self._agent_lock:
            for agent in self._agents:
                if hasattr(agent, 'get_name') and agent.get_name() == name:
                    return agent
        return None
    
    def get_agents_by_status(self, status: AgentStatus) -> List[IAgentInterface]:
        """Get agents by status"""
        with self._agent_lock:
            return [agent for agent in self._agents if agent.get_status() == status]
    
    def shutdown(self) -> None:
        """Shutdown agent manager and thread pool"""
        self.stop_all_agents()
        self._shutdown_event.set()
        AgentImpl.shutdown_executor()
    
    def is_shutdown(self) -> bool:
        """Check if manager is shutdown"""
        return self._shutdown_event.is_set()


# Convenience functions for agent creation
def create_deposit_agent(account: Account, amount: Decimal, iterations: int = -1, 
                        force_direct_notify: bool = False) -> DepositAgent:
    """Create a deposit agent"""
    return DepositAgent(account, amount, iterations, force_direct_notify)


def create_withdraw_agent(account: Account, amount: Decimal, iterations: int = -1,
                         force_direct_notify: bool = False) -> WithdrawAgent:
    """Create a withdrawal agent"""
    return WithdrawAgent(account, amount, iterations, force_direct_notify)


def create_transfer_agent(source_account: Account, target_account: Account, 
                         amount: Decimal, iterations: int = -1,
                         force_direct_notify: bool = False) -> TransferAgent:
    """Create a transfer agent"""
    return TransferAgent(source_account, target_account, amount, iterations, force_direct_notify) 