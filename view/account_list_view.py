import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Optional
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from view.tkinter_view import TkinterView
from decimal import Decimal

class AccountListView(TkinterView):
    DOLLARS = "Edit account in $"
    EUROS = "Edit account in €"
    YEN = "Edit account in ¥"
    DEPOSITAGENT = "Create Deposit agent"
    WITHDRAWAGENT = "Create Withdraw agent"
    SAVE = "Save"
    EXIT = "Exit"

    def __init__(self, model, controller):
        super().__init__(title="Account Selection")
        self._model = model
        self._controller = controller
        self._account_views: Dict[str, tk.Toplevel] = {}
        self._setup_gui()
        self._center_window()
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self._populate_account_list()

    def _setup_gui(self):
        # Account selection
        self.account_combo = ttk.Combobox(self, state="readonly")
        self.account_combo.pack(fill="x", padx=20, pady=10)
        self.account_combo.bind("<<ComboboxSelected>>", lambda e: self._on_account_selected())
        # Currency edit buttons
        currency_frame = ttk.Frame(self)
        currency_frame.pack(fill="x", padx=20, pady=5)
        self.dollar_btn = ttk.Button(currency_frame, text=self.DOLLARS, command=lambda: self._open_account_view("USD"))
        self.euro_btn = ttk.Button(currency_frame, text=self.EUROS, command=lambda: self._open_account_view("EUR"))
        self.yen_btn = ttk.Button(currency_frame, text=self.YEN, command=lambda: self._open_account_view("JPY"))
        self.dollar_btn.grid(row=0, column=0, padx=5, pady=3)
        self.euro_btn.grid(row=0, column=1, padx=5, pady=3)
        self.yen_btn.grid(row=0, column=2, padx=5, pady=3)
        # Agent creation buttons
        agent_frame = ttk.Frame(self)
        agent_frame.pack(fill="x", padx=20, pady=5)
        self.deposit_agent_btn = ttk.Button(agent_frame, text=self.DEPOSITAGENT, command=self._create_deposit_agent)
        self.withdraw_agent_btn = ttk.Button(agent_frame, text=self.WITHDRAWAGENT, command=self._create_withdraw_agent)
        self.deposit_agent_btn.grid(row=0, column=0, padx=5, pady=3)
        self.withdraw_agent_btn.grid(row=0, column=1, padx=5, pady=3)
        # Save/Exit buttons
        command_frame = ttk.Frame(self)
        command_frame.pack(fill="x", padx=20, pady=10)
        self.save_btn = ttk.Button(command_frame, text=self.SAVE, command=self._save_accounts)
        self.exit_btn = ttk.Button(command_frame, text=self.EXIT, command=self._exit_application)
        self.save_btn.grid(row=0, column=0, padx=5, pady=3, sticky="w")
        self.exit_btn.grid(row=0, column=1, padx=5, pady=3, sticky="e")

    def _center_window(self):
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _populate_account_list(self):
        accounts = self.get_model().list_accounts() if hasattr(self.get_model(), 'list_accounts') else []
        self.account_combo['values'] = accounts
        if accounts:
            self.account_combo.current(0)
        self._update_button_states(bool(accounts))

    def _update_button_states(self, enabled: bool):
        state = 'normal' if enabled else 'disabled'
        for btn in [self.dollar_btn, self.euro_btn, self.yen_btn, self.deposit_agent_btn, self.withdraw_agent_btn]:
            btn.config(state=state)

    def _on_account_selected(self):
        # Could update UI or enable/disable buttons if needed
        pass

    def _get_selected_account(self):
        idx = self.account_combo.current()
        accounts = self.account_combo['values']
        if idx < 0 or not accounts:
            messagebox.showerror("Selection Error", "No account selected.")
            return None
        account_name = accounts[idx]
        if hasattr(self.get_model(), 'get_account_by_name'):
            return self.get_model().get_account_by_name(account_name)
        return None

    def _open_account_view(self, currency_type: str):
        selected_account = self._get_selected_account()
        if selected_account:
            key = f"{selected_account}_{currency_type}"
            if key in self._account_views:
                # Bring existing window to front
                window = self._account_views[key]
                window.lift()
                window.focus_force()
                return
            try:
                from .account_view import AccountView
                from controller.mvc_controller import AccountController
                controller = AccountController(selected_account)
                view = AccountView(selected_account, controller, currency_type)
                controller.set_view(view)
                self._account_views[key] = view
                view.protocol("WM_DELETE_WINDOW", lambda: self._on_child_window_close(key))
                view.show()
            except Exception as e:
                messagebox.showerror("Window Error", f"Failed to open account view: {str(e)}")

    def _on_child_window_close(self, key):
        if key in self._account_views:
            try:
                self._account_views[key].destroy()
            except Exception:
                pass
            del self._account_views[key]

    def _create_deposit_agent(self):
        selected_account = self._get_selected_account()
        if selected_account:
            try:
                from .agent_view import AgentView
                from controller.mvc_controller import AgentController
                from agent_system import DepositAgent
                agent = DepositAgent(selected_account, Decimal("30.00"))
                controller = AgentController(agent)
                view = AgentView(agent, controller, selected_account.name)
                controller.set_view(view)
                view.show()
            except Exception as e:
                messagebox.showerror("Agent Error", f"Failed to create deposit agent: {str(e)}")

    def _create_withdraw_agent(self):
        selected_account = self._get_selected_account()
        if selected_account:
            try:
                from .agent_view import AgentView
                from controller.mvc_controller import AgentController
                from agent_system import WithdrawAgent
                agent = WithdrawAgent(selected_account, Decimal("30.00"))
                controller = AgentController(agent)
                view = AgentView(agent, controller, selected_account.name)
                controller.set_view(view)
                view.show()
            except Exception as e:
                messagebox.showerror("Agent Error", f"Failed to create withdraw agent: {str(e)}")

    def _save_accounts(self):
        try:
            self.get_controller().save_accounts()
            messagebox.showinfo("Success", "Accounts saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save accounts: {str(e)}")

    def _exit_application(self):
        try:
            if hasattr(self.get_model(), 'exit'):
                self.get_model().exit()
            for key in list(self._account_views.keys()):
                try:
                    self._account_views[key].destroy()
                except Exception:
                    pass
                del self._account_views[key]
            self.destroy()
            sys.exit(0)
        except Exception as e:
            messagebox.showerror("Error", f"Error during exit: {str(e)}")
            sys.exit(1)

    def _on_closing(self):
        self._exit_application()

    def get_model(self):
        return self._model

    def get_controller(self):
        return self._controller

    def show(self):
        self.deiconify()

# Main application entry point

def main():
    filename = "accounts.txt"
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    try:
        try:
            from model.account_model import AccountList
            from controller.mvc_controller import AccountListController
        except ImportError:
            from model.account_model import AccountList
            from controller.mvc_controller import AccountListController
        model = AccountList(filename)
        controller = AccountListController(model)
        root = tk.Tk()
        root.withdraw()
        view = AccountListView(model, controller)
        controller.set_view(view)
        view.show()
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Startup Error", f"Failed to start application: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 