import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from decimal import Decimal
from typing import Any

from view.base_view import FrameView, SpringUtilities
from account_model import ModelEvent, EventKind, AgentStatus


class AccountView(FrameView):
    """MANDATORY: GUI for a single account"""
    
    def __init__(self, parent: tk.Misc, controller: Any, **kwargs):
        super().__init__(parent, **kwargs)
        self._controller = controller
        self._controller.set_view(self)
        
        # CRITICAL: Build layout with ttk widgets only
        self._build_ui()
        self._update_display()
    
    def _build_ui(self) -> None:
        """Build the user interface"""
        # Configure grid weights for responsive layout
        self.configure_grid_weights([0, 0, 0, 0, 1], [1, 1])
        
        # Account header
        account = self._controller.get_model()
        if account:
            title_label = SpringUtilities.create_title_label(self, f"{account.name} ({account.account_id})")
            title_label.grid(row=0, column=0, columnspan=2, pady=(8, 4), sticky="ew")
        
        # Balance display
        self._balance_var = tk.StringVar()
        balance_label = ttk.Label(self, textvariable=self._balance_var, style="Title.TLabel")
        balance_label.grid(row=1, column=0, columnspan=2, pady=8, sticky="ew")
        
        # Action buttons
        button_frame = ttk.Frame(self)
        button_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=4)
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        
        deposit_btn = SpringUtilities.create_action_button(button_frame, "Deposit", self._on_deposit)
        deposit_btn.grid(row=0, column=0, sticky="ew", padx=(0, 2))
        
        withdraw_btn = SpringUtilities.create_action_button(button_frame, "Withdraw", self._on_withdraw)
        withdraw_btn.grid(row=0, column=1, sticky="ew", padx=(2, 0))
        
        # Agent control buttons
        agent_frame = ttk.Frame(self)
        agent_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=4)
        agent_frame.grid_columnconfigure(0, weight=1)
        agent_frame.grid_columnconfigure(1, weight=1)
        
        start_agents_btn = ttk.Button(agent_frame, text="Start Agents", command=self._on_start_agents)
        start_agents_btn.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(4, 0))
        
        pause_btn = ttk.Button(agent_frame, text="Pause All", command=self._on_pause_agents)
        pause_btn.grid(row=1, column=0, sticky="ew", padx=(0, 2), pady=4)
        
        resume_btn = ttk.Button(agent_frame, text="Resume All", command=self._on_resume_agents)
        resume_btn.grid(row=1, column=1, sticky="ew", padx=(2, 0), pady=4)
        
        stop_btn = ttk.Button(agent_frame, text="Stop All", command=self._on_stop_agents)
        stop_btn.grid(row=2, column=0, columnspan=2, sticky="ew", pady=4)
        
        # Status display
        self._status_var = tk.StringVar()
        status_label = ttk.Label(self, textvariable=self._status_var, style="Status.TLabel")
        status_label.grid(row=4, column=0, columnspan=2, pady=4, sticky="ew")
        
        # Separator
        separator = SpringUtilities.create_separator(self)
        separator.grid(row=5, column=0, columnspan=2, sticky="ew", pady=8)
    
    def _update_display(self) -> None:
        """Update the display with current account information"""
        account = self._controller.get_model()
        if account:
            self._balance_var.set(f"Balance: ${account.balance:.2f}")
            
            # Update status
            agent_status = self._controller.get_agent_status()
            status_text = f"Agents: {agent_status['deposit_agents']} deposit, {agent_status['withdraw_agents']} withdraw"
            if agent_status['active_futures'] > 0:
                status_text += f" ({agent_status['active_futures']} active)"
            self._status_var.set(status_text)
    
    def update_from_model(self, event: ModelEvent) -> None:
        """
        MANDATORY: Thread-safe model update handling
        CRITICAL: Uses schedule_update for thread safety
        """
        if event.kind == EventKind.BALANCE_UPDATE:
            self.schedule_update(self._update_balance_display, event.balance)
        elif event.kind == EventKind.AGENT_STATUS_UPDATE:
            self.schedule_update(self._update_agent_status, event.agent_status)
        elif event.kind == EventKind.AMOUNT_TRANSFERRED_UPDATE:
            self.schedule_update(self._update_transfer_status, event.balance)
    
    def _update_balance_display(self, balance: Decimal) -> None:
        """Update balance display (called on main thread)"""
        self._balance_var.set(f"Balance: ${balance:.2f}")
    
    def _update_agent_status(self, status: AgentStatus) -> None:
        """Update agent status display (called on main thread)"""
        self._update_display()
    
    def _update_transfer_status(self, amount: Decimal) -> None:
        """Update transfer status display (called on main thread)"""
        self._update_display()
    
    def _ask_amount(self, title: str) -> Decimal:
        """Ask user for amount input"""
        amount_str = simpledialog.askstring(title, "Enter amount:")
        if not amount_str:
            raise ValueError("Amount required")
        
        try:
            amount = Decimal(amount_str)
            if amount <= 0:
                raise ValueError("Amount must be positive")
            return amount
        except (ValueError, TypeError):
            raise ValueError("Invalid amount format")
    
    def _on_deposit(self) -> None:
        """Handle deposit button click"""
        try:
            amount = self._ask_amount("Deposit")
            self._controller.deposit(amount)
        except Exception as e:
            self.show_error(str(e))
    
    def _on_withdraw(self) -> None:
        """Handle withdraw button click"""
        try:
            amount = self._ask_amount("Withdraw")
            self._controller.withdraw(amount)
        except Exception as e:
            self.show_error(str(e))
    
    def _on_start_agents(self) -> None:
        """Handle start agents button click"""
        try:
            # Start deposit and withdraw agents
            self._controller.start_deposit_agent(Decimal('10.00'), 20)
            self._controller.start_withdraw_agent(Decimal('5.00'), 15)
            self.show_info("Agents started successfully")
        except Exception as e:
            self.show_error(f"Failed to start agents: {str(e)}")
    
    def _on_pause_agents(self) -> None:
        """Handle pause agents button click"""
        try:
            self._controller.pause_all_agents()
            self.show_info("All agents paused")
        except Exception as e:
            self.show_error(f"Failed to pause agents: {str(e)}")
    
    def _on_resume_agents(self) -> None:
        """Handle resume agents button click"""
        try:
            self._controller.resume_all_agents()
            self.show_info("All agents resumed")
        except Exception as e:
            self.show_error(f"Failed to resume agents: {str(e)}")
    
    def _on_stop_agents(self) -> None:
        """Handle stop agents button click"""
        try:
            self._controller.stop_all_agents()
            self.show_info("All agents stopped")
        except Exception as e:
            self.show_error(f"Failed to stop agents: {str(e)}")
    
    def refresh_display(self) -> None:
        """Refresh the display manually"""
        self._update_display() 