from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List
from threading import RLock
import tkinter as tk
from decimal import Decimal
from concurrent.futures import Future
from account_model import (
    Account, ModelEvent, EventKind, AgentStatus, 
    OverdrawException, InterruptedException
)
from agent_system import (
    DepositAgent, WithdrawAgent, AgentImpl, 
    create_deposit_agent, create_withdraw_agent
)


class Controller(ABC):
    """
    MANDATORY: Base controller interface for MVC pattern
    """
    @abstractmethod
    def set_model(self, model: Any) -> None:
        """CRITICAL: Set the model reference"""
        pass
    
    @abstractmethod
    def get_model(self) -> Any:
        """MANDATORY: Get current model"""
        pass
    
    @abstractmethod
    def set_view(self, view: Any) -> None:
        """CRITICAL: Set the view reference"""
        pass
    
    @abstractmethod
    def get_view(self) -> Any:
        """MANDATORY: Get current view"""
        pass


class AbstractController(Controller):
    """
    MANDATORY: Base implementation with thread safety
    """
    def __init__(self):
        self._model = None
        self._view = None
        self._lock = RLock()
        
    def set_model(self, model: Any) -> None:
        """CRITICAL: Thread-safe model assignment"""
        with self._lock:
            if self._model is not None:
                # MANDATORY: Remove existing listeners
                self._model.remove_listener(self._on_model_changed)
            
            self._model = model
            
            if self._model is not None:
                # CRITICAL: Add new listener
                self._model.add_listener(self._on_model_changed)
    
    def get_model(self) -> Any:
        """MANDATORY: Thread-safe model access"""
        with self._lock:
            return self._model
    
    def set_view(self, view: Any) -> None:
        """CRITICAL: Thread-safe view assignment"""
        with self._lock:
            self._view = view
            if self._view is not None:
                self._view.set_controller(self)
    
    def get_view(self) -> Any:
        """MANDATORY: Thread-safe view access"""
        with self._lock:
            return self._view
    
    def _on_model_changed(self, event: ModelEvent) -> None:
        """CRITICAL: Handle model change notifications"""
        if self._view is not None:
            # MANDATORY: Update view on main thread
            self._view.update_from_model(event)
    
    def _handle_error(self, error_message: str) -> None:
        """CRITICAL: Handle errors and notify view"""
        print(f"ERROR: {error_message}")  # Log error
        if self._view is not None:
            self._view.show_error(error_message)


class AccountController(AbstractController):
    """
    CRITICAL: Controller for individual account operations
    """
    def __init__(self, account: Account):
        super().__init__()
        self.set_model(account)
        self._deposit_agents: List[DepositAgent] = []
        self._withdraw_agents: List[WithdrawAgent] = []
        self._agent_futures: List[Future] = []
        self._agent_lock = RLock()
        
    def deposit(self, amount: Decimal) -> None:
        """
        MANDATORY: Handle deposit request from view
        CRITICAL: Must validate input and handle errors
        """
        try:
            if amount <= 0:
                raise ValueError("Deposit amount must be positive")
            
            account = self.get_model()
            if account is not None:
                account.deposit(amount)
                
        except Exception as e:
            self._handle_error(f"Deposit failed: {str(e)}")
    
    def withdraw(self, amount: Decimal) -> None:
        """
        MANDATORY: Handle withdrawal request from view
        CRITICAL: Must handle OverdrawException properly
        """
        try:
            if amount <= 0:
                raise ValueError("Withdrawal amount must be positive")
            
            account = self.get_model()
            if account is not None:
                account.withdraw(amount)
                
        except OverdrawException as e:
            self._handle_error(f"Insufficient funds: {str(e)}")
        except Exception as e:
            self._handle_error(f"Withdrawal failed: {str(e)}")
    
    def transfer(self, target_account: Optional[Account], amount: Decimal) -> None:
        """
        CRITICAL: Handle transfer request with proper error handling
        """
        try:
            if amount <= 0:
                raise ValueError("Transfer amount must be positive")
            if target_account is None:
                raise ValueError("Target account cannot be None")
            
            account = self.get_model()
            if account is not None:
                account.transfer(target_account, amount)
                
        except Exception as e:
            self._handle_error(f"Transfer failed: {str(e)}")
    
    def start_deposit_agent(self, amount: Decimal, iterations: int = -1) -> None:
        """
        MANDATORY: Start automated deposit agent
        CRITICAL: Must track agent lifecycle
        """
        try:
            account = self.get_model()
            if account is not None:
                agent = create_deposit_agent(account, amount, iterations, force_direct_notify=True)
                with self._agent_lock:
                    self._deposit_agents.append(agent)
                    future = AgentImpl.execute_agent(agent)
                    self._agent_futures.append(future)
                
        except Exception as e:
            self._handle_error(f"Failed to start deposit agent: {str(e)}")
    
    def start_withdraw_agent(self, amount: Decimal, iterations: int = -1) -> None:
        """
        MANDATORY: Start automated withdrawal agent
        CRITICAL: Must track agent lifecycle
        """
        try:
            account = self.get_model()
            if account is not None:
                agent = create_withdraw_agent(account, amount, iterations, force_direct_notify=True)
                with self._agent_lock:
                    self._withdraw_agents.append(agent)
                    future = AgentImpl.execute_agent(agent)
                    self._agent_futures.append(future)
                
        except Exception as e:
            self._handle_error(f"Failed to start withdraw agent: {str(e)}")
    
    def pause_all_agents(self) -> None:
        """CRITICAL: Pause all running agents"""
        with self._agent_lock:
            for agent in self._deposit_agents + self._withdraw_agents:
                agent.on_pause()
    
    def resume_all_agents(self) -> None:
        """CRITICAL: Resume all paused agents"""
        with self._agent_lock:
            for agent in self._deposit_agents + self._withdraw_agents:
                agent.on_resume()
    
    def stop_all_agents(self) -> None:
        """MANDATORY: Stop all agents and cleanup resources"""
        with self._agent_lock:
            for agent in self._deposit_agents + self._withdraw_agents:
                agent.stop()
            
            # CRITICAL: Cancel futures
            for future in self._agent_futures:
                if not future.done():
                    future.cancel()
            
            self._deposit_agents.clear()
            self._withdraw_agents.clear()
            self._agent_futures.clear()
    
    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents"""
        with self._agent_lock:
            status = {
                'deposit_agents': len(self._deposit_agents),
                'withdraw_agents': len(self._withdraw_agents),
                'active_futures': len([f for f in self._agent_futures if not f.done()]),
                'deposit_agents_status': [agent.get_status().value for agent in self._deposit_agents],
                'withdraw_agents_status': [agent.get_status().value for agent in self._withdraw_agents]
            }
        return status


class AccountListController(AbstractController):
    """
    MANDATORY: Controller for managing multiple accounts
    """
    def __init__(self):
        super().__init__()
        self._account_controllers: Dict[str, AccountController] = {}
        self._account_lock = RLock()
        
    def add_account(self, name: str, account_id: str, initial_balance: Decimal) -> AccountController:
        """
        CRITICAL: Add new account with controller
        MANDATORY: Must validate uniqueness and create proper bindings
        """
        with self._account_lock:
            if account_id in self._account_controllers:
                raise ValueError(f"Account with ID {account_id} already exists")
            
            try:
                account = Account(name, account_id, initial_balance, force_direct_notify=True)
                controller = AccountController(account)
                self._account_controllers[account_id] = controller
                
                # MANDATORY: Notify view of new account
                if self._view is not None:
                    self._view.add_account_view(controller)
                
                return controller
                
            except Exception as e:
                self._handle_error(f"Failed to create account: {str(e)}")
                raise
    
    def remove_account(self, account_id: str) -> None:
        """
        CRITICAL: Remove account and cleanup resources
        """
        with self._account_lock:
            if account_id not in self._account_controllers:
                raise ValueError(f"Account with ID {account_id} not found")
            
            try:
                controller = self._account_controllers[account_id]
                controller.stop_all_agents()  # MANDATORY: Stop all agents
                
                del self._account_controllers[account_id]
                
                # MANDATORY: Notify view
                if self._view is not None:
                    self._view.remove_account_view(account_id)
                    
            except Exception as e:
                self._handle_error(f"Failed to remove account: {str(e)}")
    
    def get_account_controller(self, account_id: str) -> Optional[AccountController]:
        """MANDATORY: Get controller for specific account"""
        with self._account_lock:
            return self._account_controllers.get(account_id)
    
    def get_all_accounts(self) -> List[AccountController]:
        """CRITICAL: Get all account controllers"""
        with self._account_lock:
            return list(self._account_controllers.values())
    
    def transfer_between_accounts(self, source_id: str, target_id: str, amount: Decimal) -> None:
        """
        CRITICAL: Handle inter-account transfers
        MANDATORY: Must validate accounts exist and handle errors
        """
        with self._account_lock:
            source_controller = self._account_controllers.get(source_id)
            target_controller = self._account_controllers.get(target_id)
            
            if source_controller is None:
                raise ValueError(f"Source account {source_id} not found")
            if target_controller is None:
                raise ValueError(f"Target account {target_id} not found")
            
            source_account = source_controller.get_model()
            target_account = target_controller.get_model()
            
            source_controller.transfer(target_account, amount)
    
    def get_account_summary(self) -> Dict[str, Any]:
        """Get summary of all accounts"""
        with self._account_lock:
            summary = {
                'total_accounts': len(self._account_controllers),
                'accounts': {}
            }
            
            for account_id, controller in self._account_controllers.items():
                account = controller.get_model()
                if account is not None:
                    summary['accounts'][account_id] = {
                        'name': account.name,
                        'balance': str(account.balance),
                        'agent_status': controller.get_agent_status()
                    }
            
            return summary
    
    def pause_all_agents(self) -> None:
        """Pause all agents across all accounts"""
        with self._account_lock:
            for controller in self._account_controllers.values():
                controller.pause_all_agents()
    
    def resume_all_agents(self) -> None:
        """Resume all agents across all accounts"""
        with self._account_lock:
            for controller in self._account_controllers.values():
                controller.resume_all_agents()
    
    def stop_all_agents(self) -> None:
        """Stop all agents across all accounts"""
        with self._account_lock:
            for controller in self._account_controllers.values():
                controller.stop_all_agents()


class AgentController(AbstractController):
    """
    CRITICAL: Controller for managing agent operations across accounts
    """
    def __init__(self, account_list_controller: AccountListController):
        super().__init__()
        self._account_list_controller = account_list_controller
        self._test_running = False
        self._test_lock = RLock()
    
    def start_concurrent_test(self, deposit_amount: Decimal = Decimal('10.00'), 
                            withdraw_amount: Decimal = Decimal('5.00'),
                            iterations: int = 20) -> None:
        """
        MANDATORY: Start comprehensive concurrency test
        CRITICAL: Must create realistic multi-threaded scenarios
        """
        with self._test_lock:
            if self._test_running:
                self._handle_error("Test already running")
                return
            
            self._test_running = True
            
            try:
                accounts = self._account_list_controller.get_all_accounts()
                if not accounts:
                    self._handle_error("No accounts available for testing")
                    return
                
                for controller in accounts:
                    # CRITICAL: Start multiple agents per account
                    controller.start_deposit_agent(deposit_amount, iterations)
                    controller.start_withdraw_agent(withdraw_amount, iterations // 2)
                
                # MANDATORY: Notify view
                if self._view is not None:
                    self._view.on_test_started(len(accounts))
                    
            except Exception as e:
                self._test_running = False
                self._handle_error(f"Failed to start concurrent test: {str(e)}")
    
    def stop_concurrent_test(self) -> None:
        """Stop the concurrent test"""
        with self._test_lock:
            if not self._test_running:
                return
            
            try:
                self._account_list_controller.stop_all_agents()
                self._test_running = False
                
                # MANDATORY: Notify view
                if self._view is not None:
                    self._view.on_test_stopped()
                    
            except Exception as e:
                self._handle_error(f"Failed to stop concurrent test: {str(e)}")
    
    def is_test_running(self) -> bool:
        """Check if test is currently running"""
        with self._test_lock:
            return self._test_running
    
    def get_test_status(self) -> Dict[str, Any]:
        """Get current test status"""
        with self._test_lock:
            accounts = self._account_list_controller.get_all_accounts()
            total_agents = 0
            active_agents = 0
            
            for controller in accounts:
                status = controller.get_agent_status()
                total_agents += status['deposit_agents'] + status['withdraw_agents']
                active_agents += status['active_futures']
            
            return {
                'test_running': self._test_running,
                'total_accounts': len(accounts),
                'total_agents': total_agents,
                'active_agents': active_agents
            }
    
    def stop_all_operations(self) -> None:
        """MANDATORY: Emergency stop for all operations"""
        try:
            self.stop_concurrent_test()
            AgentImpl.shutdown_executor()
            
            # MANDATORY: Notify view
            if self._view is not None:
                self._view.on_emergency_stop()
                
        except Exception as e:
            self._handle_error(f"Emergency stop failed: {str(e)}")


class MainController(AbstractController):
    """
    MANDATORY: Main controller coordinating all other controllers
    """
    def __init__(self):
        super().__init__()
        self._account_list_controller = AccountListController()
        self._agent_controller = AgentController(self._account_list_controller)
        
        # CRITICAL: Set up controller hierarchy
        self._account_list_controller.set_view(self._view)
        self._agent_controller.set_view(self._view)
    
    def set_view(self, view: Any) -> None:
        """Override to set view for all sub-controllers"""
        super().set_view(view)
        self._account_list_controller.set_view(view)
        self._agent_controller.set_view(view)
    
    def get_account_list_controller(self) -> AccountListController:
        """Get account list controller"""
        return self._account_list_controller
    
    def get_agent_controller(self) -> AgentController:
        """Get agent controller"""
        return self._agent_controller
    
    def initialize_default_accounts(self) -> None:
        """Initialize some default accounts for testing"""
        try:
            self._account_list_controller.add_account("Savings", "SAV001", Decimal("1000.00"))
            self._account_list_controller.add_account("Checking", "CHK001", Decimal("500.00"))
            self._account_list_controller.add_account("Investment", "INV001", Decimal("2500.00"))
        except Exception as e:
            self._handle_error(f"Failed to initialize default accounts: {str(e)}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'accounts': self._account_list_controller.get_account_summary(),
            'agent_test': self._agent_controller.get_test_status(),
            'thread_pool': {
                'active_tasks': AgentImpl.get_active_tasks_count()
            }
        }
    
    def shutdown(self) -> None:
        """MANDATORY: Graceful shutdown of entire system"""
        try:
            # Stop all agents
            self._agent_controller.stop_all_operations()
            
            # Shutdown thread pool
            AgentImpl.shutdown_executor()
            
            # MANDATORY: Notify view
            if self._view is not None:
                self._view.on_system_shutdown()
                
        except Exception as e:
            self._handle_error(f"Shutdown failed: {str(e)}")


# Convenience functions for controller creation
def create_account_controller(account: Account) -> AccountController:
    """Create an account controller"""
    return AccountController(account)


def create_account_list_controller() -> AccountListController:
    """Create an account list controller"""
    return AccountListController()


def create_agent_controller(account_list_controller: AccountListController) -> AgentController:
    """Create an agent controller"""
    return AgentController(account_list_controller)


def create_main_controller() -> MainController:
    """Create the main controller"""
    return MainController() 