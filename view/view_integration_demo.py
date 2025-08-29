"""
CRITICAL: View Package Integration Demo

This demo showcases the complete view package integration with:
- Thread-safe multi-window management
- MVC architecture coordination
- Currency management system
- Error handling framework
- Observer pattern implementation

MANDATORY: Demonstrates all critical integration features.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from decimal import Decimal
from typing import Any

from view import (
    ViewManager, WindowCoordinator, view_manager, window_coordinator,
    CurrencyManager, currency_manager,
    ViewErrorHandler, view_error_handler,
    AccountView, AccountListView
)
from account_model import Account, ModelEvent, EventKind
from mvc_controller import AccountController


class MockAccount(Account):
    """Mock account for demonstration"""
    
    def __init__(self, account_id: str, name: str, initial_balance: Decimal = Decimal("1000.00")):
        super().__init__(name, account_id, initial_balance)
    
    def get_id(self) -> str:
        return self.account_id
    
    def simulate_balance_change(self, change: Decimal):
        """Simulate balance change for demo purposes"""
        # Use deposit or withdraw methods to properly update balance
        if change > 0:
            self.deposit(change)
        else:
            self.withdraw(abs(change))


class IntegrationDemoApp:
    """
    CRITICAL: Complete integration demonstration
    MANDATORY: Shows all view package features working together
    """
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("View Package Integration Demo")
        self.root.geometry("800x600")
        
        # CRITICAL: Initialize global managers
        self.setup_managers()
        
        # MANDATORY: Create demo accounts and controllers
        self.setup_demo_data()
        
        # CRITICAL: Build the demo interface
        self.build_interface()
        
        # MANDATORY: Setup event handlers
        self.setup_event_handlers()
        
        print("Integration Demo initialized successfully")
    
    def setup_managers(self):
        """Setup global managers"""
        # Currency manager is already initialized globally
        # Register this app for currency updates
        currency_manager.register_observer(self.on_currency_rate_changed)
        
        # Error handler is already initialized globally
        # Register custom error callbacks
        view_error_handler.register_error_callback("ValueError", self.handle_value_error)
        view_error_handler.register_error_callback("ConnectionError", self.handle_connection_error)
    
    def setup_demo_data(self):
        """Create demo accounts and controllers"""
        self.accounts = {
            "ACC001": MockAccount("ACC001", "Demo Account 1", Decimal("1500.00")),
            "ACC002": MockAccount("ACC002", "Demo Account 2", Decimal("2500.00")),
            "ACC003": MockAccount("ACC003", "Demo Account 3", Decimal("3000.00"))
        }
        
        self.controllers = {}
        for account_id, account in self.accounts.items():
            controller = AccountController(account)
            self.controllers[account_id] = controller
    
    def build_interface(self):
        """Build the main demo interface"""
        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=0)  # Title
        self.root.grid_rowconfigure(1, weight=0)  # Controls
        self.root.grid_rowconfigure(2, weight=0)  # Status
        self.root.grid_rowconfigure(3, weight=1)  # Log
        self.root.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(self.root, text="View Package Integration Demo", 
                               font=("Segoe UI", 16, "bold"))
        title_label.grid(row=0, column=0, pady=10, sticky="ew")
        
        # Control buttons
        control_frame = ttk.Frame(self.root)
        control_frame.grid(row=1, column=0, pady=10, sticky="ew")
        control_frame.grid_columnconfigure(0, weight=1)
        control_frame.grid_columnconfigure(1, weight=1)
        control_frame.grid_columnconfigure(2, weight=1)
        control_frame.grid_columnconfigure(3, weight=1)
        
        # Account management buttons
        ttk.Button(control_frame, text="Open Account 1", 
                  command=lambda: self.open_account_window("ACC001")).grid(row=0, column=0, padx=5)
        ttk.Button(control_frame, text="Open Account 2", 
                  command=lambda: self.open_account_window("ACC002")).grid(row=0, column=1, padx=5)
        ttk.Button(control_frame, text="Open Account 3", 
                  command=lambda: self.open_account_window("ACC003")).grid(row=0, column=2, padx=5)
        ttk.Button(control_frame, text="Cascade Windows", 
                  command=self.cascade_windows).grid(row=0, column=3, padx=5)
        
        # Currency and error testing buttons
        ttk.Button(control_frame, text="Update EUR Rate", 
                  command=self.update_eur_rate).grid(row=1, column=0, padx=5, pady=5)
        ttk.Button(control_frame, text="Test Currency Conversion", 
                  command=self.test_currency_conversion).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(control_frame, text="Simulate Error", 
                  command=self.simulate_error).grid(row=1, column=2, padx=5, pady=5)
        ttk.Button(control_frame, text="Background Update", 
                  command=self.start_background_update).grid(row=1, column=3, padx=5, pady=5)
        
        # Status display
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(self.root, textvariable=self.status_var, 
                                font=("Segoe UI", 10))
        status_label.grid(row=2, column=0, pady=5, sticky="ew")
        
        # Log display
        log_frame = ttk.Frame(self.root)
        log_frame.grid(row=3, column=0, pady=10, sticky="nsew")
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
        ttk.Label(log_frame, text="Activity Log:").grid(row=0, column=0, sticky="w")
        
        self.log_text = tk.Text(log_frame, height=15, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=1, column=0, sticky="nsew")
        scrollbar.grid(row=1, column=1, sticky="ns")
    
    def setup_event_handlers(self):
        """Setup event handlers"""
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def log_message(self, message: str):
        """Add message to log"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        print(message)
    
    def open_account_window(self, account_id: str):
        """Open account window using window coordinator"""
        try:
            account = self.accounts[account_id]
            controller = self.controllers[account_id]
            
            # Use window coordinator to prevent duplicates
            window = window_coordinator.open_account_view(account, controller)
            
            # Register with view manager
            view_id = f"account_{account_id}"
            view_manager.register_view(view_id, window, 
                                     lambda: self.log_message(f"Account {account_id} window closed"))
            
            self.log_message(f"Opened account window: {account_id}")
            self.update_status(f"Account {account_id} opened")
            
        except Exception as e:
            self.log_message(f"Error opening account window: {e}")
            view_error_handler.handle_view_error(self, e, "open_account_window")
    
    def cascade_windows(self):
        """Cascade all open windows"""
        try:
            window_coordinator.cascade_windows()
            self.log_message("Windows cascaded")
            self.update_status("Windows arranged")
        except Exception as e:
            self.log_message(f"Error cascading windows: {e}")
    
    def update_eur_rate(self):
        """Update EUR exchange rate"""
        try:
            import random
            new_rate = Decimal(str(random.uniform(0.80, 0.90)))
            currency_manager.update_exchange_rate("EUR", new_rate)
            self.log_message(f"Updated EUR rate to: {new_rate}")
            self.update_status(f"EUR rate: {new_rate}")
        except Exception as e:
            self.log_message(f"Error updating EUR rate: {e}")
    
    def test_currency_conversion(self):
        """Test currency conversion"""
        try:
            amount = Decimal("100.00")
            converted = currency_manager.convert_amount(amount, "USD", "EUR")
            formatted = currency_manager.format_amount(converted, "EUR")
            self.log_message(f"Currency conversion: $100.00 = {formatted}")
            self.update_status(f"Conversion: {formatted}")
        except Exception as e:
            self.log_message(f"Error in currency conversion: {e}")
    
    def simulate_error(self):
        """Simulate various errors"""
        try:
            import random
            error_types = [
                ValueError("Invalid input data"),
                ConnectionError("Network connection failed"),
                FileNotFoundError("Configuration file not found"),
                PermissionError("Access denied")
            ]
            
            error = random.choice(error_types)
            self.log_message(f"Simulating error: {type(error).__name__}")
            view_error_handler.handle_view_error(self, error, "simulation")
            
        except Exception as e:
            self.log_message(f"Error in error simulation: {e}")
    
    def start_background_update(self):
        """Start background thread to update account balances"""
        def background_update():
            try:
                for i in range(5):
                    time.sleep(2)
                    # Update random account balance
                    import random
                    account_id = random.choice(list(self.accounts.keys()))
                    account = self.accounts[account_id]
                    
                    # Simulate balance change
                    change = Decimal(str(random.uniform(-100, 100)))
                    account.simulate_balance_change(change)
                    
                    self.log_message(f"Background update: {account_id} balance changed by {change:+.2f}")
                    
            except Exception as e:
                self.log_message(f"Background update error: {e}")
        
        thread = threading.Thread(target=background_update, daemon=True)
        thread.start()
        self.log_message("Started background balance updates")
        self.update_status("Background updates active")
    
    def update_status(self, message: str):
        """Update status display"""
        self.status_var.set(message)
    
    # Currency observer interface
    def on_currency_rate_changed(self, currency: str, rate: Decimal):
        """Handle currency rate changes"""
        self.log_message(f"Currency rate changed: {currency} = {rate}")
    
    # Error handling callbacks
    def handle_value_error(self, view: Any, error: Exception):
        """Handle value errors"""
        self.log_message(f"Value error handled: {error}")
        self.update_status("Value error resolved")
    
    def handle_connection_error(self, view: Any, error: Exception):
        """Handle connection errors"""
        self.log_message(f"Connection error handled: {error}")
        self.update_status("Connection error resolved")
    
    def on_closing(self):
        """Handle application closing"""
        try:
            self.log_message("Closing application...")
            
            # Close all managed windows
            window_coordinator.close_all_windows()
            
            # Unregister from currency manager
            currency_manager.unregister_observer(self.on_currency_rate_changed)
            
            # Get final statistics
            view_stats = view_manager.get_view_statistics()
            window_stats = window_coordinator.get_window_statistics()
            currency_stats = currency_manager.get_currency_statistics()
            error_stats = view_error_handler.get_error_statistics()
            
            self.log_message(f"Final statistics:")
            self.log_message(f"  Views: {view_stats['total_views']}")
            self.log_message(f"  Windows: {window_stats['total_windows']}")
            self.log_message(f"  Currencies: {currency_stats['total_currencies']}")
            self.log_message(f"  Errors: {error_stats['total_errors']}")
            
            self.root.destroy()
            
        except Exception as e:
            print(f"Error during shutdown: {e}")
            self.root.destroy()


def main():
    """Main function"""
    try:
        app = IntegrationDemoApp()
        app.root.mainloop()
    except Exception as e:
        print(f"Error starting demo: {e}")
        messagebox.showerror("Demo Error", f"Failed to start demo: {e}")


if __name__ == "__main__":
    main() 