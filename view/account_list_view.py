import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from decimal import Decimal
from typing import Any, Dict

from view.base_view import FrameView, SpringUtilities
from view.account_view import AccountView
from account_model import ModelEvent, EventKind


class AccountListView(FrameView):
    """MANDATORY: Main application window showing all accounts"""
    
    def __init__(self, root: tk.Tk, controller: Any):
        super().__init__(root)
        self._controller = controller
        self._controller.set_view(self)
        self._account_views: Dict[str, AccountView] = {}
        
        # CRITICAL: Build layout with ttk widgets only
        self._build_ui()
    
    def _build_ui(self) -> None:
        """Build the user interface"""
        # Configure grid weights for responsive layout
        self.configure_grid_weights([0, 1, 0], [1])
        
        # Title
        title_label = SpringUtilities.create_title_label(self, "Account Manager")
        title_label.grid(row=0, column=0, pady=(8, 16), sticky="ew")
        
        # Main content area
        main_frame = ttk.Frame(self)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=8, pady=4)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Scrollable accounts frame
        self._create_scrollable_accounts_frame(main_frame)
        
        # Control buttons
        control_frame = ttk.Frame(self)
        control_frame.grid(row=2, column=0, sticky="ew", padx=8, pady=8)
        control_frame.grid_columnconfigure(0, weight=1)
        control_frame.grid_columnconfigure(1, weight=1)
        control_frame.grid_columnconfigure(2, weight=1)
        control_frame.grid_columnconfigure(3, weight=1)
        
        # Add account button
        add_btn = SpringUtilities.create_action_button(control_frame, "Add Account", self._on_add_account)
        add_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        
        # Test controls
        test_btn = ttk.Button(control_frame, text="Start Test", command=self._on_start_test)
        test_btn.grid(row=0, column=1, sticky="ew", padx=2)
        
        stop_test_btn = ttk.Button(control_frame, text="Stop Test", command=self._on_stop_test)
        stop_test_btn.grid(row=0, column=2, sticky="ew", padx=2)
        
        # System controls
        system_btn = ttk.Button(control_frame, text="System Status", command=self._on_system_status)
        system_btn.grid(row=0, column=3, sticky="ew", padx=(4, 0))
        
        # Status bar
        self._status_var = tk.StringVar()
        status_label = ttk.Label(self, textvariable=self._status_var, style="Status.TLabel")
        status_label.grid(row=3, column=0, pady=4, sticky="ew")
        self._status_var.set("Ready")
    
    def _create_scrollable_accounts_frame(self, parent: ttk.Frame) -> None:
        """Create scrollable frame for accounts"""
        # Create canvas and scrollbar
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        
        # Configure canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create accounts frame inside canvas
        self._accounts_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=self._accounts_frame, anchor="nw")
        
        # Pack scrollbar and canvas
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        
        # Configure canvas scrolling
        self._accounts_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas.find_withtag("all")[0], width=e.width))
        
        # Mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def add_account_view(self, account_controller: Any) -> None:
        """Add account view to the display"""
        account = account_controller.get_model()
        if account:
            # Create account view
            account_view = AccountView(self._accounts_frame, account_controller, relief="groove", borderwidth=2)
            account_view.pack(fill="x", pady=4, padx=4)
            
            # Store reference
            self._account_views[account.account_id] = account_view
            
            # Update status
            self._update_status()
    
    def remove_account_view(self, account_id: str) -> None:
        """Remove account view from the display"""
        if account_id in self._account_views:
            account_view = self._account_views[account_id]
            account_view.destroy()
            del self._account_views[account_id]
            
            # Update status
            self._update_status()
    
    def _update_status(self) -> None:
        """Update status display"""
        account_count = len(self._account_views)
        self._status_var.set(f"Accounts: {account_count}")
    
    def update_from_model(self, event: ModelEvent) -> None:
        """
        MANDATORY: Thread-safe model update handling
        CRITICAL: Uses schedule_update for thread safety
        """
        # Update status
        self.schedule_update(self._update_status)
    
    def _on_add_account(self) -> None:
        """Handle add account button click"""
        try:
            # Get account details from user
            account_id = simpledialog.askstring("New Account", "Account ID:")
            if not account_id:
                return
            
            name = simpledialog.askstring("New Account", "Account name:")
            if not name:
                return
            
            balance_str = simpledialog.askstring("New Account", "Initial balance:")
            if not balance_str:
                return
            
            try:
                balance = Decimal(balance_str)
                if balance < 0:
                    raise ValueError("Balance cannot be negative")
            except (ValueError, TypeError):
                self.show_error("Invalid balance format")
                return
            
            # Add account through controller
            self._controller.add_account(name, account_id, balance)
            self.show_info(f"Account '{name}' created successfully")
            
        except Exception as e:
            self.show_error(f"Failed to create account: {str(e)}")
    
    def _on_start_test(self) -> None:
        """Handle start test button click"""
        try:
            agent_controller = self._controller.get_agent_controller()
            if agent_controller:
                agent_controller.start_concurrent_test(Decimal('10.00'), Decimal('5.00'), 10)
                self.show_info("Concurrent test started")
            else:
                self.show_error("Agent controller not available")
        except Exception as e:
            self.show_error(f"Failed to start test: {str(e)}")
    
    def _on_stop_test(self) -> None:
        """Handle stop test button click"""
        try:
            agent_controller = self._controller.get_agent_controller()
            if agent_controller:
                agent_controller.stop_concurrent_test()
                self.show_info("Concurrent test stopped")
            else:
                self.show_error("Agent controller not available")
        except Exception as e:
            self.show_error(f"Failed to stop test: {str(e)}")
    
    def _on_system_status(self) -> None:
        """Handle system status button click"""
        try:
            status = self._controller.get_system_status()
            
            # Create status dialog
            status_text = self._format_system_status(status)
            
            # Show status in dialog
            dialog = tk.Toplevel(self)
            dialog.title("System Status")
            dialog.geometry("500x400")
            dialog.transient(self)
            dialog.grab_set()
            
            # Create text widget for status
            text_widget = tk.Text(dialog, wrap="word", padx=10, pady=10)
            text_widget.pack(fill="both", expand=True)
            text_widget.insert("1.0", status_text)
            text_widget.config(state="disabled")
            
            # Close button
            close_btn = ttk.Button(dialog, text="Close", command=dialog.destroy)
            close_btn.pack(pady=10)
            
        except Exception as e:
            self.show_error(f"Failed to get system status: {str(e)}")
    
    def _format_system_status(self, status: dict) -> str:
        """Format system status for display"""
        lines = []
        lines.append("=== SYSTEM STATUS ===\n")
        
        # Account information
        accounts = status.get('accounts', {})
        lines.append(f"Total Accounts: {accounts.get('total_accounts', 0)}")
        lines.append("")
        
        # Individual account details
        for account_id, account_info in accounts.get('accounts', {}).items():
            lines.append(f"Account: {account_info['name']} ({account_id})")
            lines.append(f"  Balance: ${account_info['balance']}")
            
            agent_status = account_info.get('agent_status', {})
            lines.append(f"  Agents: {agent_status.get('deposit_agents', 0)} deposit, {agent_status.get('withdraw_agents', 0)} withdraw")
            lines.append(f"  Active: {agent_status.get('active_futures', 0)}")
            lines.append("")
        
        # Agent test information
        agent_test = status.get('agent_test', {})
        lines.append("=== AGENT TEST STATUS ===")
        lines.append(f"Test Running: {agent_test.get('test_running', False)}")
        lines.append(f"Total Agents: {agent_test.get('total_agents', 0)}")
        lines.append(f"Active Agents: {agent_test.get('active_agents', 0)}")
        lines.append("")
        
        # Thread pool information
        thread_pool = status.get('thread_pool', {})
        lines.append("=== THREAD POOL STATUS ===")
        lines.append(f"Active Tasks: {thread_pool.get('active_tasks', 0)}")
        
        return "\n".join(lines)
    
    def refresh_all_accounts(self) -> None:
        """Refresh all account displays"""
        for account_view in self._account_views.values():
            account_view.refresh_display()
    
    def on_test_started(self, account_count: int) -> None:
        """Handle test started event"""
        self.schedule_update(self._status_var.set, f"Test running on {account_count} accounts")
    
    def on_test_stopped(self) -> None:
        """Handle test stopped event"""
        self.schedule_update(self._status_var.set, "Test stopped")
    
    def on_emergency_stop(self) -> None:
        """Handle emergency stop event"""
        self.schedule_update(self._status_var.set, "Emergency stop executed")
    
    def on_system_shutdown(self) -> None:
        """Handle system shutdown event"""
        self.schedule_update(self._status_var.set, "System shutdown") 