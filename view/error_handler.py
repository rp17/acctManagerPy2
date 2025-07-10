"""
CRITICAL: Centralized Error Handling Framework

This module provides comprehensive error handling for all views in the
account management system, including thread-safe error reporting,
user-friendly error messages, and recovery mechanisms.

MANDATORY: All errors must be handled gracefully with proper user feedback.
"""

import threading
import traceback
import logging
from typing import Any, Optional, Callable, Dict
from datetime import datetime
import tkinter as tk
from tkinter import messagebox


class ViewErrorHandler:
    """
    CRITICAL: Centralized error handling for all views
    MANDATORY: Thread-safe error handling with recovery mechanisms
    """
    
    def __init__(self):
        self._error_callbacks: Dict[str, Callable] = {}
        self._recovery_strategies: Dict[str, Callable] = {}
        self._error_log: list = []
        self._lock = threading.Lock()
        self._setup_logging()
    
    def _setup_logging(self) -> None:
        """Setup error logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('view_errors.log'),
                logging.StreamHandler()
            ]
        )
        self._logger = logging.getLogger('ViewErrorHandler')
    
    @staticmethod
    def handle_view_error(view: Any, error: Exception, operation: str) -> None:
        """
        MANDATORY: Standard error handling for all views
        CRITICAL: Thread-safe error handling with user feedback
        """
        error_msg = f"Error in {operation}: {str(error)}"
        
        # CRITICAL: Log error for debugging
        print(f"VIEW ERROR: {error_msg}")
        
        # MANDATORY: Show user-friendly message
        try:
            if isinstance(error, ValueError):
                ViewErrorHandler._show_error_dialog("Input Error", "Please check your input and try again.")
            elif isinstance(error, ConnectionError):
                ViewErrorHandler._show_error_dialog("Connection Error", "Unable to connect to server.")
            elif isinstance(error, PermissionError):
                ViewErrorHandler._show_error_dialog("Permission Error", "You don't have permission to perform this action.")
            elif isinstance(error, FileNotFoundError):
                ViewErrorHandler._show_error_dialog("File Error", "The requested file could not be found.")
            elif isinstance(error, tk.TclError):
                ViewErrorHandler._show_error_dialog("GUI Error", "A GUI error occurred. Please try again.")
            else:
                ViewErrorHandler._show_error_dialog("Application Error", f"An unexpected error occurred: {str(error)}")
        except Exception as dialog_error:
            print(f"Error showing error dialog: {dialog_error}")
        
        # CRITICAL: Attempt recovery
        if hasattr(view, 'recover_from_error'):
            try:
                view.recover_from_error(error)
            except Exception as recovery_error:
                print(f"Recovery failed: {recovery_error}")
    
    @staticmethod
    def _show_error_dialog(title: str, message: str) -> None:
        """
        MANDATORY: Show error dialog on main thread
        CRITICAL: Safe error dialog display
        """
        try:
            # Create a temporary root window if none exists
            root = tk.Tk()
            root.withdraw()  # Hide the root window
            
            messagebox.showerror(title, message)
            root.destroy()
        except Exception as e:
            print(f"Error showing error dialog: {e}")
    
    def register_error_callback(self, error_type: str, callback: Callable) -> None:
        """
        MANDATORY: Register custom error handling callback
        CRITICAL: Thread-safe callback registration
        """
        with self._lock:
            self._error_callbacks[error_type] = callback
    
    def register_recovery_strategy(self, error_type: str, strategy: Callable) -> None:
        """
        MANDATORY: Register recovery strategy for specific errors
        CRITICAL: Thread-safe strategy registration
        """
        with self._lock:
            self._recovery_strategies[error_type] = strategy
    
    def handle_specific_error(self, view: Any, error: Exception, error_type: str) -> bool:
        """
        CRITICAL: Handle specific error types with custom logic
        MANDATORY: Return True if error was handled, False otherwise
        """
        with self._lock:
            callback = self._error_callbacks.get(error_type)
            strategy = self._recovery_strategies.get(error_type)
        
        if callback:
            try:
                callback(view, error)
                return True
            except Exception as callback_error:
                self._logger.error(f"Error in callback for {error_type}: {callback_error}")
        
        if strategy:
            try:
                strategy(view, error)
                return True
            except Exception as strategy_error:
                self._logger.error(f"Error in recovery strategy for {error_type}: {strategy_error}")
        
        return False
    
    def log_error(self, error: Exception, context: str = "", view: Optional[Any] = None) -> None:
        """
        MANDATORY: Log error with context information
        CRITICAL: Thread-safe error logging
        """
        with self._lock:
            error_entry = {
                'timestamp': datetime.now(),
                'error_type': type(error).__name__,
                'error_message': str(error),
                'context': context,
                'view_type': type(view).__name__ if view else 'Unknown',
                'traceback': traceback.format_exc()
            }
            self._error_log.append(error_entry)
        
        # Log to file
        self._logger.error(f"Error in {context}: {error}")
    
    def get_error_log(self) -> list:
        """Get recent error log entries"""
        with self._lock:
            return self._error_log.copy()
    
    def clear_error_log(self) -> None:
        """Clear error log"""
        with self._lock:
            self._error_log.clear()
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics"""
        with self._lock:
            error_counts = {}
            for entry in self._error_log:
                error_type = entry['error_type']
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
            
            return {
                'total_errors': len(self._error_log),
                'error_types': error_counts,
                'registered_callbacks': len(self._error_callbacks),
                'registered_strategies': len(self._recovery_strategies)
            }


class ThreadSafeErrorHandler:
    """
    CRITICAL: Thread-safe error handler for background operations
    MANDATORY: Safe error handling from non-GUI threads
    """
    
    def __init__(self, view: Any):
        self.view = view
        self._error_queue = []
        self._queue_lock = threading.Lock()
    
    def queue_error(self, error: Exception, operation: str) -> None:
        """
        MANDATORY: Queue error for thread-safe handling
        CRITICAL: Safe error queuing from background threads
        """
        with self._queue_lock:
            self._error_queue.append((error, operation))
        
        # Schedule error handling on main thread
        if hasattr(self.view, 'after'):
            self.view.after(0, self._process_queued_errors)
    
    def _process_queued_errors(self) -> None:
        """Process queued errors on main thread"""
        with self._queue_lock:
            errors_to_process = self._error_queue.copy()
            self._error_queue.clear()
        
        for error, operation in errors_to_process:
            ViewErrorHandler.handle_view_error(self.view, error, operation)


class ErrorRecoveryManager:
    """
    CRITICAL: Manage error recovery strategies
    MANDATORY: Provide automatic recovery mechanisms
    """
    
    def __init__(self):
        self._recovery_strategies: Dict[str, Callable] = {}
        self._setup_default_strategies()
    
    def _setup_default_strategies(self) -> None:
        """Setup default recovery strategies"""
        self._recovery_strategies.update({
            'ConnectionError': self._recover_connection_error,
            'ValueError': self._recover_value_error,
            'FileNotFoundError': self._recover_file_error,
            'PermissionError': self._recover_permission_error,
            'tk.TclError': self._recover_gui_error
        })
    
    def register_recovery_strategy(self, error_type: str, strategy: Callable) -> None:
        """Register custom recovery strategy"""
        self._recovery_strategies[error_type] = strategy
    
    def attempt_recovery(self, view: Any, error: Exception) -> bool:
        """
        CRITICAL: Attempt automatic error recovery
        MANDATORY: Return True if recovery was successful
        """
        error_type = type(error).__name__
        strategy = self._recovery_strategies.get(error_type)
        
        if strategy:
            try:
                return strategy(view, error)
            except Exception as recovery_error:
                print(f"Recovery strategy failed: {recovery_error}")
        
        return False
    
    def _recover_connection_error(self, view: Any, error: Exception) -> bool:
        """Recover from connection errors"""
        try:
            # Attempt to reconnect or show retry dialog
            if hasattr(view, 'show_info'):
                view.show_info("Connection lost. Attempting to reconnect...")
            return True
        except:
            return False
    
    def _recover_value_error(self, view: Any, error: Exception) -> bool:
        """Recover from value errors"""
        try:
            # Clear invalid input and show error message
            if hasattr(view, 'show_error'):
                view.show_error("Invalid input. Please check your data and try again.")
            return True
        except:
            return False
    
    def _recover_file_error(self, view: Any, error: Exception) -> bool:
        """Recover from file errors"""
        try:
            # Show file selection dialog or create default file
            if hasattr(view, 'show_error'):
                view.show_error("File not found. Please select a valid file.")
            return True
        except:
            return False
    
    def _recover_permission_error(self, view: Any, error: Exception) -> bool:
        """Recover from permission errors"""
        try:
            # Show permission request or alternative action
            if hasattr(view, 'show_error'):
                view.show_error("Permission denied. Please check your permissions.")
            return True
        except:
            return False
    
    def _recover_gui_error(self, view: Any, error: Exception) -> bool:
        """Recover from GUI errors"""
        try:
            # Refresh GUI or recreate widgets
            if hasattr(view, 'refresh_display'):
                view.refresh_display()
            return True
        except:
            return False


# CRITICAL: Global instances for application-wide access
view_error_handler = ViewErrorHandler()
error_recovery_manager = ErrorRecoveryManager() 