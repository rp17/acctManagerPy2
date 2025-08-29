import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal, ROUND_HALF_EVEN, InvalidOperation
from typing import Optional, Dict
from enum import Enum
from .tkinter_view import TkinterView

class Currency(Enum):
    DOLLAR = "USD"
    EURO = "EUR"
    YEN = "JPY"

class AccountView(tk.Frame, TkinterView):
    exchange_rates: Dict[str, Decimal] = {
        "USD": Decimal("1.0"),
        "EUR": Decimal("0.79"),
        "JPY": Decimal("94.1")
    }
    reverse_rates: Dict[str, Decimal] = {
        "USD": Decimal("1.0"),
        "EUR": Decimal("1") / Decimal("0.79"),
        "JPY": Decimal("1") / Decimal("94.1")
    }
    currency_symbols: Dict[str, str] = {
        "USD": "$",
        "EUR": "€",
        "JPY": "¥"
    }

    def __init__(self, master, model, controller, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        # Optionally set the window title if master supports it
        if hasattr(master, 'title'):
            master.title("AccountView")
        self._model = model
        self._controller = controller
        self.currency_type = Currency(currency_type)
        self._balance_var = tk.StringVar(value="0.00")
        self._amount_var = tk.StringVar(value="30.00")
        symbol = self.currency_symbols[self.currency_type.value]
        self.title(f"Account operations in {symbol}")
        self._setup_gui()
        self._center_window()
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self._register_with_model()

    def _setup_gui(self):
        # Title frame
        self.label_frame = ttk.LabelFrame(self, text=self._get_account_name())
        self.label_frame.pack(fill="both", expand=True, padx=10, pady=10)
        # Form panel
        self.form_panel = ttk.Frame(self.label_frame)
        self.form_panel.pack(fill="x", padx=10, pady=10)
        # Balance
        self.balance_label = ttk.Label(self.form_panel, text="Balance:")
        self.balance_field = ttk.Entry(self.form_panel, textvariable=self._balance_var, state="readonly", width=20)
        # Amount
        self.amount_label = ttk.Label(self.form_panel, text="Amount:")
        self.amount_entry = ttk.Entry(self.form_panel, textvariable=self._amount_var, width=20)
        # Layout
        self.balance_label.grid(row=0, column=0, sticky="e", padx=5, pady=3)
        self.balance_field.grid(row=0, column=1, sticky="w", padx=5, pady=3)
        self.amount_label.grid(row=1, column=0, sticky="e", padx=5, pady=3)
        self.amount_entry.grid(row=1, column=1, sticky="w", padx=5, pady=3)
        # Button panel
        self.button_panel = ttk.Frame(self.label_frame)
        self.button_panel.pack(fill="x", padx=10, pady=10)
        self.deposit_button = ttk.Button(self.button_panel, text="Deposit", command=self._on_deposit)
        self.withdraw_button = ttk.Button(self.button_panel, text="Withdraw", command=self._on_withdraw)
        self.deposit_button.grid(row=0, column=0, padx=5, pady=3)
        self.withdraw_button.grid(row=0, column=1, padx=5, pady=3)
        # Accessibility: Tab order
        self.amount_entry.focus_set()
        self.amount_entry.bind('<Return>', lambda e: self._on_deposit())
        self.withdraw_button.bind('<Return>', lambda e: self._on_withdraw())

    def _get_account_name(self):
        if hasattr(self._model, 'name'):
            return str(self._model.name)
        return "Account"

    def _center_window(self):
        self.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
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
        # Thread-safe model update
        event_kind = getattr(event, 'kind', None)
        if event_kind and str(event_kind).endswith("BALANCE_UPDATE"):
            balance = getattr(event, 'balance', None)
            self._schedule_gui_update(self._update_balance_display, balance)

    def update_from_model(self, event):
        # Minimal implementation for interface compliance
        pass

    def _update_balance_display(self, balance):
        try:
            display_balance = self._convert_to_display_currency(balance)
            symbol = self.currency_symbols[self.currency_type.value]
            self._balance_var.set(f"{symbol}{display_balance:,.2f}")
        except Exception:
            self._balance_var.set("0.00")

    def _convert_to_display_currency(self, amount: Decimal) -> Decimal:
        if self.currency_type != Currency.DOLLAR:
            rate = self.exchange_rates[self.currency_type.value]
            converted = amount * rate
            return converted.quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
        return amount

    def _convert_to_usd(self, amount: Decimal) -> Decimal:
        if self.currency_type != Currency.DOLLAR:
            reverse_rate = self.reverse_rates[self.currency_type.value]
            converted = amount * reverse_rate
            return converted.quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
        return amount

    def get_amount(self) -> Optional[Decimal]:
        try:
            raw_amount = Decimal(self.amount_entry.get())
            amount = self._convert_to_usd(raw_amount)
            if amount <= 0:
                raise ValueError("Amount must be positive")
            return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
        except (ValueError, InvalidOperation):
            messagebox.showerror("Input Error", "Amount field only accepts positive decimals")
            self.amount_entry.delete(0, tk.END)
            self.amount_entry.insert(0, "30.00")
            return None

    def _on_deposit(self):
        amount = self.get_amount()
        if amount and amount > 0:
            try:
                self.get_controller().operation("Deposit", amount)
            except Exception as e:
                messagebox.showerror("Operation Error", f"Deposit failed: {str(e)}")

    def _on_withdraw(self):
        amount = self.get_amount()
        if amount and amount > 0:
            try:
                self.get_controller().operation("Withdraw", amount)
            except Exception as e:
                messagebox.showerror("Operation Error", f"Withdraw failed: {str(e)}")

    def _on_closing(self):
        self.unregister_with_model()
        if hasattr(self._controller, 'set_view'):
            self._controller.set_view(None)
        self.destroy() 