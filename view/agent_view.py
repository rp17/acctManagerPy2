import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal, ROUND_HALF_EVEN, InvalidOperation
from typing import Optional, Dict
from enum import Enum
import threading
from .tkinter_view import TkinterView

class AgentStatus(Enum):
    NOT_STARTED = "Not started"
    RUNNING = "Running"
    PAUSED = "Paused"
    FINISHED = "Finished"
    ERROR = "Error"

class AgentView(TkinterView):
    START = "Start"
    PAUSE = "Pause"
    RESUME = "Resume"
    DISMISS = "Dismiss"

    def __init__(self, agent_model, controller, account_name: str):
        super().__init__(title="AgentView")
        self._model = agent_model
        self._controller = controller
        self.account_name = account_name
        self.agent_type = self._determine_agent_type(agent_model)
        self.agent_id = self._generate_agent_id()
        self._transferred_var = tk.StringVar(value="0.00")
        self._status_var = tk.StringVar(value=AgentStatus.NOT_STARTED.value)
        self._amount_var = tk.StringVar(value="30.00")
        self.title(f"{self.agent_type} agent {self.agent_id}")
        self._setup_gui()
        self._center_window()
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self._current_status = AgentStatus.NOT_STARTED
        self._register_with_model()

    def _determine_agent_type(self, agent_model):
        if hasattr(agent_model, '__class__'):
            class_name = agent_model.__class__.__name__
            if 'Deposit' in class_name:
                return "Deposit"
            elif 'Withdraw' in class_name:
                return "Withdraw"
        return "Unknown"

    def _generate_agent_id(self):
        return str(id(self._model))[-5:]

    def _setup_gui(self):
        # Title
        self.label_frame = ttk.LabelFrame(self, text=f"{self.account_name} ({self.agent_type} {self.agent_id})")
        self.label_frame.pack(fill="both", expand=True, padx=10, pady=10)
        # Form panel
        self.form_panel = ttk.Frame(self.label_frame)
        self.form_panel.pack(fill="x", padx=10, pady=10)
        # Transferred
        self.transferred_label = ttk.Label(self.form_panel, text="Transferred:")
        self.transferred_field = ttk.Entry(self.form_panel, textvariable=self._transferred_var, state="readonly", width=15)
        # Amount
        self.amount_label = ttk.Label(self.form_panel, text="Amount:")
        self.amount_entry = ttk.Entry(self.form_panel, textvariable=self._amount_var, width=15)
        # Status
        self.status_label = ttk.Label(self.form_panel, text="Status:")
        self.status_field = ttk.Entry(self.form_panel, textvariable=self._status_var, state="readonly", width=15)
        # Layout
        self.transferred_label.grid(row=0, column=0, sticky="e", padx=5, pady=3)
        self.transferred_field.grid(row=0, column=1, sticky="w", padx=5, pady=3)
        self.amount_label.grid(row=1, column=0, sticky="e", padx=5, pady=3)
        self.amount_entry.grid(row=1, column=1, sticky="w", padx=5, pady=3)
        self.status_label.grid(row=2, column=0, sticky="e", padx=5, pady=3)
        self.status_field.grid(row=2, column=1, sticky="w", padx=5, pady=3)
        # Button panel
        self.button_panel = ttk.Frame(self.label_frame)
        self.button_panel.pack(fill="x", padx=10, pady=10)
        self.start_button = ttk.Button(self.button_panel, text=self.START, command=lambda: self._handle_action(self.START))
        self.pause_button = ttk.Button(self.button_panel, text=self.PAUSE, command=lambda: self._handle_action(self.PAUSE))
        self.resume_button = ttk.Button(self.button_panel, text=self.RESUME, command=lambda: self._handle_action(self.RESUME))
        self.dismiss_button = ttk.Button(self.button_panel, text=self.DISMISS, command=lambda: self._handle_action(self.DISMISS))
        self.start_button.grid(row=0, column=0, padx=5, pady=3)
        self.pause_button.grid(row=0, column=1, padx=5, pady=3)
        self.resume_button.grid(row=0, column=2, padx=5, pady=3)
        self.dismiss_button.grid(row=0, column=3, padx=5, pady=3)
        self._update_button_states(AgentStatus.NOT_STARTED)

    def _center_window(self):
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2) - 50
        y = (screen_height // 2) - (height // 2) - 50
        self.geometry(f"{width}x{height}+{x}+{y}")

    def _register_with_model(self):
        if hasattr(self._model, 'add_listener'):
            self._model.add_listener(self.model_changed)

    def unregister_with_model(self):
        if hasattr(self._model, 'remove_listener'):
            self._model.remove_listener(self.model_changed)

    def get_model(self):
        return self._model

    def get_controller(self):
        return self._controller

    def model_changed(self, event):
        event_kind = getattr(event, 'kind', None)
        if event_kind and hasattr(event, 'balance'):
            if str(event_kind).endswith("AMOUNT_TRANSFERRED_UPDATE"):
                transferred = getattr(event, 'balance', None)
                self._schedule_gui_update(self._update_transferred_display, transferred)
            elif str(event_kind).endswith("AGENT_STATUS_UPDATE"):
                status = getattr(event, 'agent_status', None)
                self._schedule_gui_update(self._update_status_display, status)

    def _update_transferred_display(self, transferred):
        try:
            self._transferred_var.set(str(transferred))
        except Exception:
            self._transferred_var.set("0.00")

    def _update_status_display(self, status):
        try:
            if isinstance(status, Enum):
                status_value = status.value
            else:
                status_value = str(status)
            self._status_var.set(status_value)
            self._current_status = AgentStatus(status_value) if status_value in AgentStatus._value2member_map_ else AgentStatus.ERROR
            self._update_button_states(self._current_status)
        except Exception:
            self._status_var.set(AgentStatus.ERROR.value)
            self._update_button_states(AgentStatus.ERROR)

    def _update_button_states(self, status: AgentStatus):
        if status == AgentStatus.NOT_STARTED:
            self.start_button.config(state='normal')
            self.pause_button.config(state='disabled')
            self.resume_button.config(state='disabled')
            self.dismiss_button.config(state='normal')
        elif status == AgentStatus.RUNNING:
            self.start_button.config(state='disabled')
            self.pause_button.config(state='normal')
            self.resume_button.config(state='disabled')
            self.dismiss_button.config(state='normal')
        elif status == AgentStatus.PAUSED:
            self.start_button.config(state='disabled')
            self.pause_button.config(state='disabled')
            self.resume_button.config(state='normal')
            self.dismiss_button.config(state='normal')
        elif status in [AgentStatus.FINISHED, AgentStatus.ERROR]:
            self.start_button.config(state='disabled')
            self.pause_button.config(state='disabled')
            self.resume_button.config(state='disabled')
            self.dismiss_button.config(state='normal')

    def _handle_action(self, action: str):
        try:
            if action == self.START:
                amount = self.get_amount()
                if amount and amount > 0:
                    self.get_controller().start_agent(amount)
                    self._disable_start_button()
            elif action == self.PAUSE:
                self.get_controller().pause_agent()
            elif action == self.RESUME:
                self.get_controller().resume_agent()
            elif action == self.DISMISS:
                self._dismiss_agent()
        except Exception as e:
            messagebox.showerror("Agent Error", f"Operation failed: {str(e)}")

    def _disable_start_button(self):
        self.start_button.config(state='disabled')

    def _dismiss_agent(self):
        try:
            agent = self.get_model()
            if agent and hasattr(agent, 'finish'):
                agent.finish()
                print(f"AgentView: stopping {self.agent_type} agent {self.agent_id} for {self.account_name}")
            self.unregister_with_model()
            if hasattr(self.get_controller(), 'set_view'):
                self.get_controller().set_view(None)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Cleanup Error", f"Failed to dismiss agent: {str(e)}")

    def get_amount(self) -> Optional[Decimal]:
        try:
            amount = Decimal(self.amount_entry.get())
            amount = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
            if amount <= 0:
                raise ValueError("Amount must be positive")
            self.amount_entry.delete(0, tk.END)
            self.amount_entry.insert(0, str(amount))
            return amount
        except (ValueError, InvalidOperation):
            messagebox.showerror("Input Error", "Amount field only accepts positive decimals")
            self.amount_entry.delete(0, tk.END)
            self.amount_entry.insert(0, "30.00")
            return None

    def _on_closing(self):
        self._dismiss_agent() 