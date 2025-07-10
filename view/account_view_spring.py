import tkinter as tk
from tkinter import ttk
from .account_view import AccountView
from .layout_utilities import LayoutUtilities

class AccountViewSpring(AccountView):
    def __init__(self, parent, controller, currency_type: str = "USD", **kwargs):
        super().__init__(parent, controller, **kwargs)
        self.currency_type = currency_type
        self._setup_spring_layout()
        self._setup_responsive_layout()

    def _setup_spring_layout(self):
        # Remove existing layout
        for child in self.winfo_children():
            child.pack_forget()
            child.place_forget()
        # Create form container
        form_container = ttk.Frame(self)
        form_container.place(relx=0, rely=0, relwidth=1, relheight=0.5)
        # Example: create label/field pairs for balance and amount
        self.balance_label = ttk.Label(form_container, text="Balance:")
        self.balance_field = ttk.Label(form_container, textvariable=self._balance_var)
        self.amount_label = ttk.Label(form_container, text="Amount:")
        self.amount_field = ttk.Entry(form_container)
        label_widget_pairs = [
            (self.balance_label, self.balance_field),
            (self.amount_label, self.amount_field)
        ]
        LayoutUtilities.create_form_layout(form_container, label_widget_pairs)
        # Button container
        button_container = ttk.Frame(self)
        button_container.place(relx=0, rely=0.55, relwidth=1, relheight=0.2)
        self.deposit_btn = ttk.Button(button_container, text="Deposit", command=self._on_deposit)
        self.withdraw_btn = ttk.Button(button_container, text="Withdraw", command=self._on_withdraw)
        self.deposit_btn.pack(side="left", expand=True, fill="x", padx=10, pady=5)
        self.withdraw_btn.pack(side="left", expand=True, fill="x", padx=10, pady=5)
        LayoutUtilities.make_uniform_grid(button_container, 1, 2, x_pad=10)

    def _setup_responsive_layout(self):
        def on_configure(event):
            if event.widget == self:
                self._recalculate_layout()
        self.bind('<Configure>', on_configure)

    def _recalculate_layout(self):
        width = self.winfo_width()
        if width < 300:
            self._setup_compact_layout()
        else:
            self._setup_spring_layout()

    def _setup_compact_layout(self):
        # Remove all children
        for child in self.winfo_children():
            child.pack_forget()
            child.place_forget()
        # Simple vertical stack for compact mode
        label = ttk.Label(self, text="Balance:")
        label.pack(fill="x", padx=10, pady=5)
        value = ttk.Label(self, textvariable=self._balance_var)
        value.pack(fill="x", padx=10, pady=5)
        entry = ttk.Entry(self)
        entry.pack(fill="x", padx=10, pady=5)
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(btn_frame, text="Deposit", command=self._on_deposit).pack(side="left", expand=True, fill="x", padx=5)
        ttk.Button(btn_frame, text="Withdraw", command=self._on_withdraw).pack(side="left", expand=True, fill="x", padx=5) 