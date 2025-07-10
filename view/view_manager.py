"""
CRITICAL: Centralized View Management System

This module provides thread-safe view management, window coordination,
and lifecycle management for the multi-threaded account management system.

MANDATORY: All view operations must be thread-safe and properly coordinated.
"""

import threading
import time
from typing import Dict, Any, Optional, Callable
from collections import defaultdict
import tkinter as tk
from tkinter import messagebox


class ViewManager:
    """
    CRITICAL: Centralized view management with thread safety
    MANDATORY: Manages all active views and their lifecycle
    """
    
    def __init__(self):
        self._active_views: Dict[str, Any] = {}
        self._view_lock = threading.Lock()
        self._view_counters = defaultdict(int)
        self._cleanup_callbacks: Dict[str, Callable] = {}
        
    def register_view(self, view_id: str, view: Any, cleanup_callback: Optional[Callable] = None) -> None:
        """
        MANDATORY: Register view for lifecycle management
        CRITICAL: Thread-safe view registration
        """
        with self._view_lock:
            self._active_views[view_id] = view
            if cleanup_callback:
                self._cleanup_callbacks[view_id] = cleanup_callback
            self._view_counters[type(view).__name__] += 1
            print(f"Registered view: {view_id} ({type(view).__name__})")
    
    def unregister_view(self, view_id: str) -> None:
        """
        CRITICAL: Cleanup view on closure
        MANDATORY: Thread-safe view unregistration
        """
        with self._view_lock:
            if view_id in self._active_views:
                view = self._active_views.pop(view_id)
                view_type = type(view).__name__
                self._view_counters[view_type] = max(0, self._view_counters[view_type] - 1)
                
                # Execute cleanup callback if provided
                if view_id in self._cleanup_callbacks:
                    try:
                        self._cleanup_callbacks[view_id]()
                    except Exception as e:
                        print(f"Error in cleanup callback for {view_id}: {e}")
                    finally:
                        del self._cleanup_callbacks[view_id]
                
                # Unregister from model if applicable
                if hasattr(view, 'unregister_with_model'):
                    try:
                        view.unregister_with_model()
                    except Exception as e:
                        print(f"Error unregistering view from model: {e}")
                
                print(f"Unregistered view: {view_id} ({view_type})")
    
    def get_view(self, view_id: str) -> Optional[Any]:
        """Get registered view by ID"""
        with self._view_lock:
            return self._active_views.get(view_id)
    
    def get_all_views(self) -> Dict[str, Any]:
        """Get all active views"""
        with self._view_lock:
            return self._active_views.copy()
    
    def get_view_count(self, view_type: str) -> int:
        """Get count of active views of specific type"""
        with self._view_lock:
            return self._view_counters.get(view_type, 0)
    
    def broadcast_model_event(self, event: Any) -> None:
        """
        MANDATORY: Thread-safe event broadcasting
        CRITICAL: Notify all registered views of model changes
        """
        with self._view_lock:
            views_to_notify = list(self._active_views.values())
        
        for view in views_to_notify:
            try:
                if hasattr(view, 'model_changed'):
                    # Use thread-safe update mechanism
                    if hasattr(view, '_schedule_gui_update'):
                        view._schedule_gui_update(view.model_changed, event)
                    elif hasattr(view, 'schedule_update'):
                        view.schedule_update(view.model_changed, event)
                    else:
                        # Direct call if no scheduling mechanism available
                        view.model_changed(event)
            except Exception as e:
                print(f"Error broadcasting event to view {type(view).__name__}: {e}")
    
    def close_all_views(self) -> None:
        """
        CRITICAL: Close all active views
        MANDATORY: Proper cleanup of all resources
        """
        with self._view_lock:
            views_to_close = list(self._active_views.items())
        
        for view_id, view in views_to_close:
            try:
                if hasattr(view, 'on_closing'):
                    view.on_closing()
                elif hasattr(view, 'destroy'):
                    view.destroy()
            except Exception as e:
                print(f"Error closing view {view_id}: {e}")
            finally:
                self.unregister_view(view_id)
    
    def get_view_statistics(self) -> Dict[str, Any]:
        """Get statistics about active views"""
        with self._view_lock:
            return {
                'total_views': len(self._active_views),
                'view_types': dict(self._view_counters),
                'active_view_ids': list(self._active_views.keys())
            }


class WindowCoordinator:
    """
    CRITICAL: Manage multiple windows and prevent conflicts
    MANDATORY: Coordinate window positioning and prevent duplicates
    """
    
    def __init__(self):
        self._account_windows: Dict[str, Any] = {}  # account_id -> AccountView
        self._agent_windows: Dict[str, Any] = {}    # agent_id -> AgentView
        self._main_window: Optional[Any] = None
        self._position_offset = 0
        self._window_lock = threading.Lock()
    
    def open_account_view(self, account: Any, controller: Any, currency_type: str = "USD") -> Any:
        """
        MANDATORY: Prevent duplicate account windows
        CRITICAL: Thread-safe window management
        """
        account_id = str(account.get_id()) if hasattr(account, 'get_id') else str(id(account))
        window_key = f"{account_id}_{currency_type}"
        
        with self._window_lock:
            if window_key in self._account_windows:
                # CRITICAL: Bring existing window to front
                existing_window = self._account_windows[window_key]
                try:
                    existing_window.lift()
                    existing_window.focus_force()
                    return existing_window
                except Exception as e:
                    print(f"Error bringing window to front: {e}")
                    # Remove stale reference
                    del self._account_windows[window_key]
            
            # MANDATORY: Create new window
            from .account_view import AccountView
            # Create a Toplevel window to contain the AccountView
            window = tk.Toplevel()
            window.title(f"Account {account_id} - {currency_type}")
            window.geometry("400x500")
            
            # Create the AccountView inside the window
            view = AccountView(window, controller)
            view.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            self._account_windows[window_key] = window
            
            # CRITICAL: Setup cleanup callback
            def on_close():
                with self._window_lock:
                    if window_key in self._account_windows:
                        del self._account_windows[window_key]
                window.destroy()
            
            window.protocol("WM_DELETE_WINDOW", on_close)
            return window
    
    def open_agent_view(self, agent: Any, controller: Any) -> Any:
        """
        MANDATORY: Prevent duplicate agent windows
        CRITICAL: Thread-safe agent window management
        """
        agent_id = str(agent.get_id()) if hasattr(agent, 'get_id') else str(id(agent))
        
        with self._window_lock:
            if agent_id in self._agent_windows:
                # CRITICAL: Bring existing window to front
                existing_window = self._agent_windows[agent_id]
                try:
                    existing_window.lift()
                    existing_window.focus_force()
                    return existing_window
                except Exception as e:
                    print(f"Error bringing agent window to front: {e}")
                    # Remove stale reference
                    del self._agent_windows[agent_id]
            
            # MANDATORY: Create new agent window
            # Note: AgentView would need to be implemented
            # from .agent_view import AgentView
            # view = AgentView(agent, controller)
            # self._agent_windows[agent_id] = view
            
            # For now, return None as AgentView is not implemented
            return None
    
    def set_main_window(self, main_window: Any) -> None:
        """Set the main application window"""
        with self._window_lock:
            self._main_window = main_window
    
    def get_main_window(self) -> Optional[Any]:
        """Get the main application window"""
        with self._window_lock:
            return self._main_window
    
    def cascade_windows(self) -> None:
        """
        CRITICAL: Arrange windows in cascade pattern
        MANDATORY: Prevent window overlap
        """
        offset = 30
        with self._window_lock:
            all_windows = list(self._account_windows.values()) + list(self._agent_windows.values())
        
        for i, window in enumerate(all_windows):
            try:
                x = 100 + (i * offset)
                y = 100 + (i * offset)
                window.geometry(f"+{x}+{y}")
            except Exception as e:
                print(f"Error cascading window: {e}")
    
    def tile_windows(self) -> None:
        """
        CRITICAL: Arrange windows in tile pattern
        MANDATORY: Efficient screen space usage
        """
        with self._window_lock:
            all_windows = list(self._account_windows.values()) + list(self._agent_windows.values())
        
        if not all_windows:
            return
        
        # Calculate grid layout
        import math
        num_windows = len(all_windows)
        cols = math.ceil(math.sqrt(num_windows))
        rows = math.ceil(num_windows / cols)
        
        screen_width = 1920  # Default, will be updated
        screen_height = 1080  # Default, will be updated
        
        try:
            screen_width = all_windows[0].winfo_screenwidth()
            screen_height = all_windows[0].winfo_screenheight()
        except:
            pass
        
        window_width = screen_width // cols
        window_height = screen_height // rows
        
        for i, window in enumerate(all_windows):
            try:
                row = i // cols
                col = i % cols
                x = col * window_width
                y = row * window_height
                window.geometry(f"{window_width}x{window_height}+{x}+{y}")
            except Exception as e:
                print(f"Error tiling window: {e}")
    
    def close_all_windows(self) -> None:
        """
        CRITICAL: Close all managed windows
        MANDATORY: Proper cleanup of all window resources
        """
        with self._window_lock:
            windows_to_close = list(self._account_windows.values()) + list(self._agent_windows.values())
        
        for window in windows_to_close:
            try:
                if hasattr(window, 'on_closing'):
                    window.on_closing()
                elif hasattr(window, 'destroy'):
                    window.destroy()
            except Exception as e:
                print(f"Error closing window: {e}")
        
        # Clear all references
        with self._window_lock:
            self._account_windows.clear()
            self._agent_windows.clear()
    
    def get_window_statistics(self) -> Dict[str, Any]:
        """Get statistics about managed windows"""
        with self._window_lock:
            return {
                'account_windows': len(self._account_windows),
                'agent_windows': len(self._agent_windows),
                'total_windows': len(self._account_windows) + len(self._agent_windows),
                'account_window_keys': list(self._account_windows.keys()),
                'agent_window_keys': list(self._agent_windows.keys())
            }


# CRITICAL: Global instances for application-wide access
view_manager = ViewManager()
window_coordinator = WindowCoordinator() 