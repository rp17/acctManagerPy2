#!/usr/bin/env python3
"""
Demonstration of the Python Account Management System

This script demonstrates all critical features:
- Thread-safe operations
- Deadlock prevention
- Precise decimal arithmetic
- Observer pattern with GUI integration
- Agent-based operations
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from decimal import Decimal
from account_model import (
    Account, IAgent, AgentStatus, OverdrawException, 
    InterruptedException, EventKind, ModelEvent
)


class AccountManagerGUI:
    """GUI demonstration of the Account Management System"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Python Account Management System - Demo")
        self.root.geometry("800x600")
        
        # Create accounts
        self.accounts = {
            "ACC001": Account("John's Account", "ACC001", Decimal("1000.00")),
            "ACC002": Account("Jane's Account", "ACC002", Decimal("500.00")),
            "ACC003": Account("Business Account", "ACC003", Decimal("2500.00"))
        }
        
        # Create agents
        self.agents = {
            "Agent1": IAgent("Trading Agent 1"),
            "Agent2": IAgent("Trading Agent 2"),
            "Agent3": IAgent("Payment Agent")
        }
        
        # Setup GUI
        self.setup_gui()
        self.setup_event_listeners()
        
        # Start background operations
        self.start_background_operations()
    
    def setup_gui(self):
        """Setup the GUI components"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Account Management System", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Account selection
        ttk.Label(main_frame, text="Select Account:").grid(row=1, column=0, sticky="w")
        self.account_var = tk.StringVar(value="ACC001")
        account_combo = ttk.Combobox(main_frame, textvariable=self.account_var, 
                                    values=list(self.accounts.keys()), state="readonly")
        account_combo.grid(row=1, column=1, sticky="ew", padx=(10, 0))
        account_combo.bind('<<ComboboxSelected>>', self.update_account_display)
        
        # Account info frame
        info_frame = ttk.LabelFrame(main_frame, text="Account Information", padding="10")
        info_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        info_frame.columnconfigure(1, weight=1)
        
        self.balance_label = ttk.Label(info_frame, text="Balance: $1000.00")
        self.balance_label.grid(row=0, column=0, columnspan=2, sticky="w")
        
        self.name_label = ttk.Label(info_frame, text="Name: John's Account")
        self.name_label.grid(row=1, column=0, columnspan=2, sticky="w")
        
        # Operations frame
        ops_frame = ttk.LabelFrame(main_frame, text="Operations", padding="10")
        ops_frame.grid(row=3, column=0, columnspan=3, sticky="nsew", pady=(10, 0))
        ops_frame.columnconfigure(1, weight=1)
        
        # Deposit section
        ttk.Label(ops_frame, text="Deposit:").grid(row=0, column=0, sticky="w")
        self.deposit_var = tk.StringVar(value="100.00")
        deposit_entry = ttk.Entry(ops_frame, textvariable=self.deposit_var)
        deposit_entry.grid(row=0, column=1, sticky="ew", padx=(10, 10))
        ttk.Button(ops_frame, text="Deposit", command=self.deposit).grid(row=0, column=2)
        
        # Withdrawal section
        ttk.Label(ops_frame, text="Withdraw:").grid(row=1, column=0, sticky="w")
        self.withdraw_var = tk.StringVar(value="50.00")
        withdraw_entry = ttk.Entry(ops_frame, textvariable=self.withdraw_var)
        withdraw_entry.grid(row=1, column=1, sticky="ew", padx=(10, 10))
        ttk.Button(ops_frame, text="Withdraw", command=self.withdraw).grid(row=1, column=2)
        
        # Transfer section
        ttk.Label(ops_frame, text="Transfer to:").grid(row=2, column=0, sticky="w")
        self.transfer_target_var = tk.StringVar(value="ACC002")
        transfer_combo = ttk.Combobox(ops_frame, textvariable=self.transfer_target_var,
                                     values=list(self.accounts.keys()), state="readonly")
        transfer_combo.grid(row=2, column=1, sticky="ew", padx=(10, 10))
        
        ttk.Label(ops_frame, text="Amount:").grid(row=3, column=0, sticky="w")
        self.transfer_amount_var = tk.StringVar(value="25.00")
        transfer_entry = ttk.Entry(ops_frame, textvariable=self.transfer_amount_var)
        transfer_entry.grid(row=3, column=1, sticky="ew", padx=(10, 10))
        ttk.Button(ops_frame, text="Transfer", command=self.transfer).grid(row=3, column=2)
        
        # Auto-withdraw section
        ttk.Label(ops_frame, text="Auto-withdraw:").grid(row=4, column=0, sticky="w")
        self.auto_withdraw_var = tk.StringVar(value="200.00")
        auto_withdraw_entry = ttk.Entry(ops_frame, textvariable=self.auto_withdraw_var)
        auto_withdraw_entry.grid(row=4, column=1, sticky="ew", padx=(10, 10))
        
        self.agent_var = tk.StringVar(value="Agent1")
        agent_combo = ttk.Combobox(ops_frame, textvariable=self.agent_var,
                                  values=list(self.agents.keys()), state="readonly")
        agent_combo.grid(row=4, column=2, padx=(10, 0))
        
        ttk.Button(ops_frame, text="Start Auto-withdraw", command=self.auto_withdraw).grid(row=5, column=2, pady=(5, 0))
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Event Log", padding="10")
        log_frame.grid(row=4, column=0, columnspan=3, sticky="nsew", pady=(10, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="Status: Ready")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        ttk.Button(status_frame, text="Clear Log", command=self.clear_log).grid(row=0, column=1, padx=(20, 0))
        ttk.Button(status_frame, text="Run Stress Test", command=self.run_stress_test).grid(row=0, column=2, padx=(10, 0))
        
        # Initial display update
        self.update_account_display()
    
    def setup_event_listeners(self):
        """Setup event listeners for all accounts"""
        for account in self.accounts.values():
            account.add_listener(self.on_account_event)
    
    def on_account_event(self, event: ModelEvent):
        """Handle account events"""
        timestamp = time.strftime("%H:%M:%S")
        event_text = f"[{timestamp}] {event.kind.value}: Balance=${event.balance}, Agent={event.agent_status.value}\n"
        
        # Use after() for thread-safe GUI updates
        self.root.after(0, self.append_to_log, event_text)
        self.root.after(0, self.update_account_display)
    
    def append_to_log(self, text: str):
        """Thread-safe log append"""
        self.log_text.insert(tk.END, text)
        self.log_text.see(tk.END)
    
    def update_account_display(self, event=None):
        """Update account display information"""
        account_id = self.account_var.get()
        account = self.accounts[account_id]
        
        self.balance_label.config(text=f"Balance: ${account.balance}")
        self.name_label.config(text=f"Name: {account.name}")
        
        # Update agent status
        agent_statuses = []
        for agent_name, agent in self.agents.items():
            status = agent.get_status()
            agent_statuses.append(f"{agent_name}: {status.value}")
        
        status_text = f"Status: Ready | Agents: {', '.join(agent_statuses)}"
        self.status_label.config(text=status_text)
    
    def deposit(self):
        """Perform deposit operation"""
        try:
            account = self.accounts[self.account_var.get()]
            amount = Decimal(self.deposit_var.get())
            account.deposit(amount)
            self.append_to_log(f"Deposited ${amount} to {account.name}\n")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid amount: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Deposit failed: {e}")
    
    def withdraw(self):
        """Perform withdrawal operation"""
        try:
            account = self.accounts[self.account_var.get()]
            amount = Decimal(self.withdraw_var.get())
            account.withdraw(amount)
            self.append_to_log(f"Withdrew ${amount} from {account.name}\n")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid amount: {e}")
        except OverdrawException as e:
            messagebox.showerror("Insufficient Funds", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Withdrawal failed: {e}")
    
    def transfer(self):
        """Perform transfer operation"""
        try:
            source_account = self.accounts[self.account_var.get()]
            target_account = self.accounts[self.transfer_target_var.get()]
            amount = Decimal(self.transfer_amount_var.get())
            
            source_account.transfer(target_account, amount)
            self.append_to_log(f"Transferred ${amount} from {source_account.name} to {target_account.name}\n")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid transfer: {e}")
        except OverdrawException as e:
            messagebox.showerror("Insufficient Funds", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Transfer failed: {e}")
    
    def auto_withdraw(self):
        """Start auto-withdraw operation in background thread"""
        account = self.accounts[self.account_var.get()]
        amount = Decimal(self.auto_withdraw_var.get())
        agent = self.agents[self.agent_var.get()]
        
        def auto_withdraw_worker():
            try:
                account.auto_withdraw(amount, agent)
                self.root.after(0, self.append_to_log, f"Auto-withdraw completed: ${amount} from {account.name}\n")
            except InterruptedException as e:
                self.root.after(0, self.append_to_log, f"Auto-withdraw interrupted: {e}\n")
            except Exception as e:
                self.root.after(0, self.append_to_log, f"Auto-withdraw failed: {e}\n")
        
        thread = threading.Thread(target=auto_withdraw_worker)
        thread.daemon = True
        thread.start()
        
        self.append_to_log(f"Started auto-withdraw: ${amount} from {account.name} using {agent.name}\n")
    
    def clear_log(self):
        """Clear the event log"""
        self.log_text.delete(1.0, tk.END)
    
    def run_stress_test(self):
        """Run a stress test with multiple concurrent operations"""
        self.append_to_log("Starting stress test with concurrent operations...\n")
        
        def stress_worker(worker_id):
            for i in range(20):
                try:
                    # Random operations
                    if i % 4 == 0:
                        # Deposit
                        account = self.accounts["ACC001"]
                        account.deposit(Decimal("10.00"))
                    elif i % 4 == 1:
                        # Withdraw
                        account = self.accounts["ACC001"]
                        account.withdraw(Decimal("5.00"))
                    elif i % 4 == 2:
                        # Transfer
                        self.accounts["ACC001"].transfer(self.accounts["ACC002"], Decimal("2.00"))
                    else:
                        # Auto-withdraw
                        agent = self.agents[f"Agent{(worker_id % 3) + 1}"]
                        self.accounts["ACC003"].auto_withdraw(Decimal("50.00"), agent)
                    
                    time.sleep(0.1)
                except (OverdrawException, InterruptedException):
                    pass
        
        # Start multiple stress test threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=stress_worker, args=(i,))
            thread.daemon = True
            threads.append(thread)
            thread.start()
        
        self.append_to_log("Stress test threads started. Check the log for events.\n")
    
    def start_background_operations(self):
        """Start background operations to demonstrate the system"""
        def background_worker():
            while True:
                try:
                    # Simulate periodic deposits
                    time.sleep(5)
                    for account in self.accounts.values():
                        if account.balance < Decimal("100.00"):
                            account.deposit(Decimal("50.00"))
                            self.root.after(0, self.append_to_log, 
                                          f"Background: Deposited $50.00 to {account.name}\n")
                except Exception as e:
                    self.root.after(0, self.append_to_log, f"Background error: {e}\n")
        
        thread = threading.Thread(target=background_worker)
        thread.daemon = True
        thread.start()


def main():
    """Main function to run the demonstration"""
    print("Starting Python Account Management System Demo...")
    print("Features demonstrated:")
    print("- Thread-safe operations with RLock")
    print("- Deadlock prevention in transfers")
    print("- Precise decimal arithmetic")
    print("- Observer pattern with GUI integration")
    print("- Agent-based operations with status tracking")
    print("- Comprehensive error handling")
    print()
    
    # Create and run GUI
    root = tk.Tk()
    app = AccountManagerGUI(root)
    
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("\nDemo interrupted by user")
    except Exception as e:
        print(f"Demo error: {e}")


if __name__ == "__main__":
    main() 