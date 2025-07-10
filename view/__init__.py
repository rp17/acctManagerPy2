"""
CRITICAL: Account Management System View Package

This package provides thread-safe GUI components for the multi-threaded
account management system. All views implement the MVC pattern with
proper observer notifications and thread-safe GUI updates.

MANDATORY: All GUI updates must use tkinter.after() for thread safety.
"""

from .base_view import View, FrameView, DialogView, SpringUtilities
from .account_view import AccountView
from .account_list_view import AccountListView
from .view_manager import ViewManager, WindowCoordinator, view_manager, window_coordinator
from .currency_manager import CurrencyManager, CurrencyInfo, currency_manager
from .error_handler import ViewErrorHandler, ThreadSafeErrorHandler, ErrorRecoveryManager, view_error_handler, error_recovery_manager
from .layout_utilities import LayoutUtilities
from .account_view_spring import AccountViewSpring
from .agent_view import AgentView

# CRITICAL: Package version for compatibility tracking
__version__ = "1.0.0"

# MANDATORY: Threading safety constants
THREAD_SAFE_UPDATE_DELAY = 50  # milliseconds
MAX_CONCURRENT_VIEWS = 10

__all__ = [
    'View',
    'FrameView',
    'DialogView', 
    'SpringUtilities',
    'AccountView',
    'AccountListView',
    'ViewManager',
    'WindowCoordinator',
    'view_manager',
    'window_coordinator',
    'CurrencyManager',
    'CurrencyInfo',
    'currency_manager',
    'ViewErrorHandler',
    'ThreadSafeErrorHandler',
    'ErrorRecoveryManager',
    'view_error_handler',
    'error_recovery_manager',
    'AccountViewSpring',
    'LayoutUtilities',
    'AgentView',
] 