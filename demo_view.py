#!/usr/bin/env python3
"""
MANDATORY: View Layer Demonstration
CRITICAL: Shows the complete Tkinter View layer working with MVC architecture
"""

import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal
import threading
import time

# Import our components
from view.base_view import FrameView, SpringUtilities
from account_model import Account, ModelEvent, EventKind
from mvc_controller import AccountController, MainController


class SimpleAccountView(FrameView):
    """Simple demonstration account view"""
    
    def __init__(self, parent, controller):
        super().__init__(parent)
        self._controller = controller
        self._build_ui()
    
    def _build_ui(self):
        """Build simple UI"""
        # Title
        title = SpringUtilities.create_title_label(self, "Account Demo")
        title.grid(row=0, column=0, columnspan=2, pady=10)
        
        # Balance display
        self._balance_var = tk.StringVar(value="Balance: $0.00")
        balance_label = ttk.Label(self, textvariable=self._balance_var, style="Title.TLabel")
        balance_label.grid(row=1, column=0, columnspan=2, pady=10)
        
        # Buttons
        deposit_btn = SpringUtilities.create_action_button(self, "Deposit $10", self._on_deposit)
        deposit_btn.grid(row=2, column=0, padx=5, pady=5)
        
        withdraw_btn = SpringUtilities.create_action_button(self, "Withdraw $5", self._on_withdraw)
        withdraw_btn.grid(row=2, column=1, padx=5, pady=5)
        
        # Status
        self._status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(self, textvariable=self._status_var, style="Status.TLabel")
        status_label.grid(row=3, column=0, columnspan=2, pady=10)
    
    def _on_deposit(self):
        """Handle deposit"""
        try:
            self._controller.deposit(Decimal('10.00'))
            self._status_var.set("Deposited $10.00")
        except Exception as e:
            self.show_error(str(e))
    
    def _on_withdraw(self):
        """Handle withdraw"""
        try:
            self._controller.withdraw(Decimal('5.00'))
            self._status_var.set("Withdrew $5.00")
        except Exception as e:
            self.show_error(str(e))
    
    def update_from_model(self, event):
        """Handle model updates"""
        if event.kind == EventKind.BALANCE_UPDATE:
            self.schedule_update(self._update_balance, event.balance)
    
    def _update_balance(self, balance):
        """Update balance display"""
        self._balance_var.set(f"Balance: ${balance:.2f}")


class DemoApp:
    """Demonstration application"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("View Layer Demo")
        self.root.geometry("400x300")
        
        # Setup styling
        self._setup_styling()
        
        # Create account and controller
        self.account = Account("Demo Account", "DEMO001", Decimal('100.00'))
        self.controller = AccountController(self.account)
        
        # Create view
        self.view = SimpleAccountView(self.root, self.controller)
        self.view.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Setup periodic updates
        self._setup_demo_updates()
    
    def _setup_styling(self):
        """Setup modern styling"""
        try:
            style = ttk.Style()
            style.theme_use("clam")
            
            style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
            style.configure("Status.TLabel", font=("Segoe UI", 10))
            style.configure("Action.TButton", font=("Segoe UI", 10, "bold"))
            
        except tk.TclError:
            pass
    
    def _setup_demo_updates(self):
        """Setup demonstration updates"""
        def demo_update():
            # Simulate background updates
            def background_task():
                time.sleep(2)
                # Update balance from background thread
                new_balance = self.account.balance + Decimal('1.00')
                self.account.set_balance(new_balance)
                
                # Create event
                event = ModelEvent(EventKind.BALANCE_UPDATE, balance=new_balance, agent_status=None)
                self.view.update_from_model(event)
            
            # Start background task
            thread = threading.Thread(target=background_task, daemon=True)
            thread.start()
            
            # Schedule next demo update
            self.root.after(5000, demo_update)
        
        # Start demo updates
        self.root.after(2000, demo_update)
    
    def run(self):
        """Run the demonstration"""
        print("View Layer Demo Started")
        print("Features demonstrated:")
        print("- Thread-safe GUI updates")
        print("- MVC architecture")
        print("- Modern Tkinter styling")
        print("- Background thread integration")
        print("\nClick buttons or wait for automatic updates...")
        
        self.root.mainloop()


def main():
    """Main entry point"""
    app = DemoApp()
    app.run()


if __name__ == "__main__":
    main() 