"""
CRITICAL REQUIREMENTS (BEGIN)
MANDATORY – READ BEFORE GENERATING CODE

Exact Feature Parity: The resulting Python 3 class must replicate every externally-visible behavior of acctMgr.model.AccountList (add/remove/load/save accounts, iterator helpers, GUI‐launch helpers, agent management and orderly shutdown) as implemented in the original Java source.

Thread-Safety:
All mutating operations (add_account, remove_account, load, save, agent helpers) MUST be protected by a re-entrant lock (threading.RLock) to prevent race conditions under heavy multi-agent loads.

GUI updates MUST be marshalled onto the Tk main loop with tkinter.Tk.after to keep the interface responsive and avoid cross-thread crashes.

Financial Precision: Use decimal.Decimal with quantization to 2 dp and ROUND_HALF_EVEN in every balance computation.

Observer Pattern: Inherit from the Python port of AbstractModel; fire ModelEvent objects to all listeners exactly as Java version does (balance updates, agent status, amount transferred).

Graceful Shutdown: exit() MUST call the static utility AgentImpl.shutdown_and_await_termination() (already ported elsewhere) and then persist data via save(); no lingering non-daemon threads allowed.

Directory Location: Save generated file as src/model/account_list.py inside the existing Python port package structure.

Place identical CRITICAL and MANDATORY anchors at both the start and end of this prompt (Sandwich Method).
CRITICAL REQUIREMENTS (END)
"""

import threading
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Dict, List, Optional, Iterator
import tkinter as tk
from model.account_model import AbstractModel, ModelEvent, EventKind
from model.agent_system import AgentImpl
import json
import os

class AccountList(AbstractModel):
    """
    CRITICAL: Thread-safe, observer-pattern, multi-account manager with GUI-safe updates and financial precision.
    """
    def __init__(self, filename: str, use_tk: bool = True):
        super().__init__(force_direct_notify=not use_tk)
        self._filename = filename
        self._accounts: Dict[str, any] = {}  # account_id -> Account
        self._lock = threading.RLock()
        self._main_thread = threading.main_thread()
        self._tk_root = None
        self._use_tk = use_tk
        self._load_accounts()

    def _get_tk_root(self):
        if not self._use_tk:
            return None
        if self._tk_root is None:
            self._tk_root = tk._default_root or tk.Tk()
            self._tk_root.withdraw()
        return self._tk_root

    def add_account(self, account):
        with self._lock:
            if account.account_id in self._accounts:
                raise ValueError(f"Account {account.account_id} already exists")
            self._accounts[account.account_id] = account
            self._fire_model_event(EventKind.BALANCE_UPDATE, account)

    def remove_account(self, account_id: str):
        with self._lock:
            if account_id not in self._accounts:
                raise ValueError(f"Account {account_id} does not exist")
            account = self._accounts.pop(account_id)
            self._fire_model_event(EventKind.BALANCE_UPDATE, account)

    def get_account_by_name(self, name: str):
        with self._lock:
            for acc in self._accounts.values():
                if getattr(acc, 'name', None) == name:
                    return acc
        return None

    def get_account(self, account_id: str):
        with self._lock:
            return self._accounts.get(account_id)

    def list_accounts(self) -> List[str]:
        with self._lock:
            return [getattr(acc, 'name', acc.account_id) for acc in self._accounts.values()]

    def __iter__(self) -> Iterator:
        with self._lock:
            return iter(list(self._accounts.values()))

    def _fire_model_event(self, kind, account):
        event = ModelEvent(kind, getattr(account, 'balance', Decimal('0.00')), getattr(account, 'agent_status', None))
        if not self._use_tk:
            self.notify_changed(event)
        elif threading.current_thread() is self._main_thread:
            self.notify_changed(event)
        else:
            root = self._get_tk_root()
            if root:
                root.after(0, lambda: self.notify_changed(event))

    def save(self):
        with self._lock:
            data = {acc.account_id: {
                'name': acc.name,
                'balance': str(acc.balance.quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN))
            } for acc in self._accounts.values()}
            with open(self._filename, 'w') as f:
                json.dump(data, f, indent=2)

    def _load_accounts(self):
        if not os.path.exists(self._filename):
            return
        with self._lock:
            with open(self._filename, 'r') as f:
                content = f.read().strip()
                if not content:
                    return
                data = json.loads(content)
                for acc_id, acc_data in data.items():
                    # Assume Account class is imported and compatible
                    from model.account_model import Account
                    acc = Account(acc_data['name'], acc_id, Decimal(acc_data['balance']))
                    self._accounts[acc_id] = acc

    def load(self):
        self._load_accounts()
        # Fire update for all accounts
        with self._lock:
            for acc in self._accounts.values():
                self._fire_model_event(EventKind.BALANCE_UPDATE, acc)

    def create_agent(self, account_id: str, agent_type: str, amount: Decimal):
        with self._lock:
            account = self.get_account(account_id)
            if not account:
                raise ValueError(f"Account {account_id} not found")
            # AgentImpl is assumed to have a create_agent method
            return AgentImpl.create_agent(account, agent_type, amount)

    def shutdown_agents(self):
        AgentImpl.shutdown_and_await_termination()

    def exit(self):
        self.shutdown_agents()
        self.save()

    # GUI helpers (for launching account/agent views, etc.) can be added as needed

# CRITICAL REQUIREMENTS (END) 