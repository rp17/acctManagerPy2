#!/usr/bin/env python3
"""
Simple View Layer Demonstration
Shows basic Tkinter View functionality with thread safety
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from decimal import Decimal


class SimpleView(ttk.Frame):
    """Simple demonstration view with thread safety"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self._build_ui()
        self._setup_thread_safety()
    
    def _build_ui(self):
        """Build the user interface"""
        # Configure grid weights
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # Title
        title = ttk.Label(self, text="View Layer Demo", font=("Segoe UI", 16, "bold"))
        title.grid(row=0, column=0, pady=20)
        
        # Main content frame
        content_frame = ttk.Frame(self)
        content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)
        
        # Balance display
        self._balance_var = tk.StringVar(value="Balance: $100.00")
        balance_label = ttk.Label(content_frame, textvariable=self._balance_var, 
                                font=("Segoe UI", 14, "bold"))
        balance_label.grid(row=0, column=0, columnspan=2, pady=20)
        
        # Buttons
        deposit_btn = ttk.Button(content_frame, text="Deposit $10", 
                               command=self._on_deposit)
        deposit_btn.grid(row=1, column=0, padx=5, pady=10, sticky="ew")
        
        withdraw_btn = ttk.Button(content_frame, text="Withdraw $5", 
                                command=self._on_withdraw)
        withdraw_btn.grid(row=1, column=1, padx=5, pady=10, sticky="ew")
        
        # Status display
        self._status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(content_frame, textvariable=self._status_var,
                               font=("Segoe UI", 10))
        status_label.grid(row=2, column=0, columnspan=2, pady=10)
        
        # Auto-update button
        auto_btn = ttk.Button(content_frame, text="Start Auto Updates", 
                            command=self._on_auto_update)
        auto_btn.grid(row=3, column=0, columnspan=2, pady=10, sticky="ew")
        
        # Current balance
        self._current_balance = Decimal('100.00')
    
    def _setup_thread_safety(self):
        """Setup thread safety mechanisms"""
        self._update_queue = []
        self._auto_updating = False
    
    def schedule_update(self, callback, *args, **kwargs):
        """Schedule a thread-safe GUI update"""
        self.after(0, lambda: callback(*args, **kwargs))
    
    def show_error(self, message):
        """Show error message thread-safely"""
        self.after(0, lambda: messagebox.showerror("Error", message))
    
    def show_info(self, message):
        """Show info message thread-safely"""
        self.after(0, lambda: messagebox.showinfo("Information", message))
    
    def _on_deposit(self):
        """Handle deposit button click"""
        try:
            self._current_balance += Decimal('10.00')
            self._balance_var.set(f"Balance: ${self._current_balance:.2f}")
            self._status_var.set("Deposited $10.00")
            self.show_info("Deposit successful!")
        except Exception as e:
            self.show_error(f"Deposit failed: {e}")
    
    def _on_withdraw(self):
        """Handle withdraw button click"""
        try:
            if self._current_balance >= Decimal('5.00'):
                self._current_balance -= Decimal('5.00')
                self._balance_var.set(f"Balance: ${self._current_balance:.2f}")
                self._status_var.set("Withdrew $5.00")
                self.show_info("Withdrawal successful!")
            else:
                self.show_error("Insufficient funds!")
        except Exception as e:
            self.show_error(f"Withdrawal failed: {e}")
    
    def _on_auto_update(self):
        """Handle auto-update button click"""
        if not self._auto_updating:
            self._auto_updating = True
            self._status_var.set("Auto updates started...")
            self._start_background_updates()
        else:
            self._auto_updating = False
            self._status_var.set("Auto updates stopped")
    
    def _start_background_updates(self):
        """Start background thread for updates"""
        def background_task():
            while self._auto_updating:
                time.sleep(2)  # Wait 2 seconds
                
                # Update balance from background thread
                self._current_balance += Decimal('1.00')
                
                # Schedule GUI update thread-safely
                self.schedule_update(self._update_balance_display, self._current_balance)
        
        # Start background thread
        thread = threading.Thread(target=background_task, daemon=True)
        thread.start()
    
    def _update_balance_display(self, balance):
        """Update balance display (called on main thread)"""
        self._balance_var.set(f"Balance: ${balance:.2f}")
        self._status_var.set(f"Auto-updated: +$1.00")


class DemoApp:
    """Demonstration application"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("View Layer Demo - Thread Safety")
        self.root.geometry("400x500")
        
        # Setup styling
        self._setup_styling()
        
        # Create view
        self.view = SimpleView(self.root)
        self.view.pack(fill="both", expand=True)
        
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
        """Handle window close"""
        self.view._auto_updating = False  # Stop background updates
        self.root.destroy()
    
    def run(self):
        """Run the demonstration"""
        print("View Layer Demo Started")
        print("Features demonstrated:")
        print("- Thread-safe GUI updates")
        print("- Background thread integration")
        print("- Modern Tkinter styling")
        print("- Error handling")
        print("\nClick buttons to test functionality...")
        
        self.root.mainloop()


def main():
    """Main entry point"""
    app = DemoApp()
    app.run()


if __name__ == "__main__":
    main() 