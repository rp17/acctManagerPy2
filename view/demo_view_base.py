#!/usr/bin/env python3
"""
MANDATORY: View Base Classes Demonstration
CRITICAL: Shows TkinterView working with MVC architecture and thread safety
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from decimal import Decimal

# Import our view components
from view import View, ModelListener
from tkinter_view import TkinterView


class DemoModel:
    """Demonstration model with observer pattern"""
    
    def __init__(self):
        self.observers = []
        self.balance = Decimal('1000.00')
        self.transaction_count = 0
    
    def add_observer(self, observer):
        """Add observer to model"""
        if observer not in self.observers:
            self.observers.append(observer)
            observer.model_registered(self)
    
    def remove_observer(self, observer):
        """Remove observer from model"""
        if observer in self.observers:
            self.observers.remove(observer)
            observer.model_unregistered(self)
    
    def notify_observers(self, event):
        """Notify all observers of model change"""
        for observer in self.observers[:]:
            observer.model_changed(event)
    
    def deposit(self, amount):
        """Deposit money and notify observers"""
        self.balance += amount
        self.transaction_count += 1
        self.notify_observers({
            'type': 'balance_update',
            'balance': self.balance,
            'transaction': 'deposit',
            'amount': amount,
            'count': self.transaction_count
        })
    
    def withdraw(self, amount):
        """Withdraw money and notify observers"""
        if self.balance >= amount:
            self.balance -= amount
            self.transaction_count += 1
            self.notify_observers({
                'type': 'balance_update',
                'balance': self.balance,
                'transaction': 'withdraw',
                'amount': amount,
                'count': self.transaction_count
            })
        else:
            self.notify_observers({
                'type': 'error',
                'message': 'Insufficient funds'
            })


class DemoController:
    """Demonstration controller for MVC pattern"""
    
    def __init__(self, model):
        self.model = model
        self.view = None
    
    def set_view(self, view):
        """Set view reference"""
        self.view = view
    
    def get_model(self):
        """Get model reference"""
        return self.model
    
    def deposit(self, amount):
        """Handle deposit action"""
        try:
            self.model.deposit(amount)
        except Exception as e:
            if self.view:
                self.view.show_error(f"Deposit failed: {e}")
    
    def withdraw(self, amount):
        """Handle withdraw action"""
        try:
            self.model.withdraw(amount)
        except Exception as e:
            if self.view:
                self.view.show_error(f"Withdrawal failed: {e}")


class DemoAccountView(TkinterView):
    """Demonstration account view using TkinterView base class"""
    
    def __init__(self, title="Account Demo"):
        super().__init__(title=title)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the user interface"""
        # Configure grid weights
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Title
        title_label = ttk.Label(self, text="Account Management", 
                               font=("Segoe UI", 16, "bold"))
        title_label.grid(row=0, column=0, pady=20)
        
        # Main content frame
        content_frame = ttk.Frame(self)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        
        # Balance display
        self._balance_var = tk.StringVar(value="Balance: $0.00")
        balance_label = ttk.Label(content_frame, textvariable=self._balance_var,
                                font=("Segoe UI", 14, "bold"))
        balance_label.grid(row=0, column=0, columnspan=2, pady=20)
        
        # Transaction count
        self._count_var = tk.StringVar(value="Transactions: 0")
        count_label = ttk.Label(content_frame, textvariable=self._count_var,
                               font=("Segoe UI", 12))
        count_label.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Buttons
        deposit_btn = ttk.Button(content_frame, text="Deposit $100",
                               command=self._on_deposit)
        deposit_btn.grid(row=2, column=0, padx=5, pady=10, sticky="ew")
        
        withdraw_btn = ttk.Button(content_frame, text="Withdraw $50",
                                command=self._on_withdraw)
        withdraw_btn.grid(row=2, column=1, padx=5, pady=10, sticky="ew")
        
        # Auto-update button
        self._auto_updating = False
        self._auto_btn = ttk.Button(content_frame, text="Start Auto Updates",
                                  command=self._on_auto_update)
        self._auto_btn.grid(row=3, column=0, columnspan=2, pady=10, sticky="ew")
        
        # Status bar
        self._status_bar = self.create_status_bar()
        self.update_status("Ready")
    
    def _on_deposit(self):
        """Handle deposit button click"""
        controller = self.get_controller()
        if controller:
            controller.deposit(Decimal('100.00'))
            self.update_status("Deposit processed")
        else:
            self.show_error("No controller available")
    
    def _on_withdraw(self):
        """Handle withdraw button click"""
        controller = self.get_controller()
        if controller:
            controller.withdraw(Decimal('50.00'))
            self.update_status("Withdrawal processed")
        else:
            self.show_error("No controller available")
    
    def _on_auto_update(self):
        """Handle auto-update button click"""
        if not self._auto_updating:
            self._auto_updating = True
            self._auto_btn.config(text="Stop Auto Updates")
            self.update_status("Auto updates started")
            self._start_auto_updates()
        else:
            self._auto_updating = False
            self._auto_btn.config(text="Start Auto Updates")
            self.update_status("Auto updates stopped")
    
    def _start_auto_updates(self):
        """Start background auto-updates"""
        def auto_update_task():
            while self._auto_updating and not self.is_destroyed():
                time.sleep(3)  # Wait 3 seconds
                if self._auto_updating and not self.is_destroyed():
                    controller = self.get_controller()
                    if controller:
                        # Random deposit or withdraw
                        import random
                        if random.choice([True, False]):
                            controller.deposit(Decimal('25.00'))
                        else:
                            controller.withdraw(Decimal('15.00'))
        
        # Start background thread
        thread = threading.Thread(target=auto_update_task, daemon=True)
        thread.start()
    
    def _update_display(self, event):
        """Update display based on model event"""
        if event['type'] == 'balance_update':
            # Update balance display
            balance = event['balance']
            self._balance_var.set(f"Balance: ${balance:.2f}")
            
            # Update transaction count
            count = event['count']
            self._count_var.set(f"Transactions: {count}")
            
            # Update status
            transaction = event['transaction']
            amount = event['amount']
            self.update_status(f"{transaction.title()}: ${amount:.2f}")
            
        elif event['type'] == 'error':
            # Show error message
            self.show_error(event['message'])
    
    def _on_model_registered(self, model):
        """Handle model registration"""
        self.update_status("Model registered")
        # Update initial display
        if hasattr(model, 'balance'):
            self._balance_var.set(f"Balance: ${model.balance:.2f}")
        if hasattr(model, 'transaction_count'):
            self._count_var.set(f"Transactions: {model.transaction_count}")
    
    def _on_model_unregistered(self, model):
        """Handle model unregistration"""
        self.update_status("Model unregistered")


class DemoApp:
    """Demonstration application"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("View Base Classes Demo")
        self.root.geometry("800x600")
        
        # Setup styling
        self._setup_styling()
        
        # Create MVC components
        self.model = DemoModel()
        self.controller = DemoController(self.model)
        
        # Create view
        self.view = DemoAccountView("Account Management Demo")
        self.view.set_controller(self.controller)
        self.view.set_model(self.model)
        
        # Setup window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _setup_styling(self):
        """Setup modern styling"""
        try:
            style = ttk.Style()
            style.theme_use("clam")
        except tk.TclError:
            pass
    
    def _on_close(self):
        """Handle application close"""
        if self.view:
            self.view.on_closing()
        self.root.destroy()
    
    def run(self):
        """Run the demonstration"""
        print("View Base Classes Demo Started")
        print("Features demonstrated:")
        print("- TkinterView base class")
        print("- MVC architecture with observer pattern")
        print("- Thread-safe GUI updates")
        print("- Proper window lifecycle management")
        print("- Error handling and status updates")
        print("\nClick buttons to test functionality...")
        
        self.root.mainloop()


def main():
    """Main entry point"""
    app = DemoApp()
    app.run()


if __name__ == "__main__":
    main() 