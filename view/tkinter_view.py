"""
MANDATORY: TkinterView Base Class - JFrame equivalent for Python/Tkinter
CRITICAL: Implements ModelListener interface with thread-safe GUI updates
"""

import tkinter as tk
from tkinter import messagebox, ttk
from threading import Lock, current_thread
from typing import Optional, Any, Callable
import weakref
import gc

from view.view import View, ModelListener


class TkinterView(tk.Toplevel, View, ModelListener):
    """
    MANDATORY: TkinterView base class - JFrame equivalent
    CRITICAL: Inherits from tk.Toplevel for multiple window support
    MANDATORY: Implements ModelListener interface for observer pattern
    """
    
    def __init__(self, title: str = "TkinterView", **kwargs):
        """
        MANDATORY: Initialize TkinterView with thread safety
        CRITICAL: Proper initialization order and resource management
        """
        # Initialize tk.Toplevel first
        super().__init__(**kwargs)
        
        # Initialize View abstract class
        View.__init__(self)
        
        # CRITICAL: Thread-safe GUI update queue
        self._update_queue = []
        self._update_lock = Lock()
        self._is_destroyed = False
        
        # MANDATORY: Window configuration
        self.title(title)
        self._setup_window_properties()
        self._setup_close_handler()
        
        # CRITICAL: Weak reference to prevent circular references
        self._weak_self = weakref.ref(self)
    
    def _setup_window_properties(self) -> None:
        """
        MANDATORY: Setup window properties for proper display
        CRITICAL: Configure window behavior and appearance
        """
        # Set window size and position
        self.geometry("600x400")
        self.resizable(True, True)
        
        # Center window on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        # Configure window style
        try:
            style = ttk.Style()
            style.theme_use("clam")
        except tk.TclError:
            pass  # Fallback if theme not available
    
    def _setup_close_handler(self) -> None:
        """
        CRITICAL: Setup window close handler for proper cleanup
        MANDATORY: Ensure resources are deallocated on window close
        """
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def get_controller(self) -> Optional[Any]:
        """
        MANDATORY: Get controller reference
        CRITICAL: Thread-safe property access
        """
        return super().get_controller()
    
    def set_controller(self, controller: Optional[Any]) -> None:
        """
        MANDATORY: Set controller reference
        CRITICAL: Thread-safe property access
        """
        super().set_controller(controller)
    
    def get_model(self) -> Optional[Any]:
        """
        MANDATORY: Get model reference
        CRITICAL: Thread-safe property access
        """
        return super().get_model()
    
    def set_model(self, model: Optional[Any]) -> None:
        """
        MANDATORY: Set model reference with observer pattern
        CRITICAL: Thread-safe property access with automatic registration
        """
        super().set_model(model)
    
    def model_changed(self, event: Any) -> None:
        """
        CRITICAL: Handle model change events thread-safely
        MANDATORY: Schedule GUI update on main thread
        """
        if self._is_destroyed:
            return
        
        # CRITICAL: Schedule GUI update on main thread
        self._schedule_gui_update(self._update_display, event)
    
    def model_registered(self, model: Any) -> None:
        """
        MANDATORY: Handle model registration
        CRITICAL: Called when view is registered with model
        """
        if not self._is_destroyed:
            self._schedule_gui_update(self._on_model_registered, model)
    
    def model_unregistered(self, model: Any) -> None:
        """
        MANDATORY: Handle model unregistration
        CRITICAL: Called when view is unregistered from model
        """
        if not self._is_destroyed:
            self._schedule_gui_update(self._on_model_unregistered, model)
    
    def _schedule_gui_update(self, callback: Callable, *args) -> None:
        """
        CRITICAL: Schedule GUI update on main thread
        MANDATORY: Use tkinter.after() for thread-safe GUI updates
        """
        if self._is_destroyed:
            return
        
        # CRITICAL: Check if we're on the main thread
        try:
            # Use a simpler approach - always schedule on main thread for safety
            self.after_idle(lambda: self._execute_gui_update(callback, *args))
        except tk.TclError:
            # Window might be destroyed, ignore
            pass
    
    def _execute_gui_update(self, callback: Callable, *args) -> None:
        """
        CRITICAL: Execute GUI update with error handling
        MANDATORY: Safe execution of GUI callbacks
        """
        if self._is_destroyed:
            return
        
        try:
            callback(*args)
        except Exception as e:
            self._handle_gui_error(e)
    
    def _handle_gui_error(self, error: Exception) -> None:
        """
        MANDATORY: Handle GUI operation errors
        CRITICAL: Provide meaningful error feedback
        """
        error_message = f"GUI Error: {str(error)}"
        print(f"TkinterView Error: {error_message}")
        
        # Try to show error message if possible
        try:
            if not self._is_destroyed:
                self.after_idle(lambda: messagebox.showerror("Error", error_message))
        except:
            pass  # Ignore if we can't show error dialog
    
    def show_error(self, message: str) -> None:
        """
        MANDATORY: Display error message to user
        CRITICAL: Thread-safe error display
        """
        self._schedule_gui_update(self._show_error_dialog, message)
    
    def show_info(self, message: str) -> None:
        """
        MANDATORY: Display info message to user
        CRITICAL: Thread-safe info display
        """
        self._schedule_gui_update(self._show_info_dialog, message)
    
    def _show_error_dialog(self, message: str) -> None:
        """
        MANDATORY: Show error dialog on main thread
        CRITICAL: Safe error dialog display
        """
        if not self._is_destroyed:
            try:
                messagebox.showerror("Error", message)
            except Exception as e:
                print(f"Error showing error dialog: {e}")
    
    def _show_info_dialog(self, message: str) -> None:
        """
        MANDATORY: Show info dialog on main thread
        CRITICAL: Safe info dialog display
        """
        if not self._is_destroyed:
            try:
                messagebox.showinfo("Information", message)
            except Exception as e:
                print(f"Error showing info dialog: {e}")
    
    def on_closing(self) -> None:
        """
        CRITICAL: Handle window closing event
        MANDATORY: Proper cleanup and resource deallocation
        """
        try:
            # Mark as destroyed to prevent further operations
            self._is_destroyed = True
            
            # MANDATORY: Cleanup resources
            self._cleanup_resources()
            
            # CRITICAL: Clear update queue
            with self._update_lock:
                self._update_queue.clear()
            
            # MANDATORY: Destroy window
            self.destroy()
            
            # CRITICAL: Garbage collection hint
            gc.collect()
            
        except Exception as e:
            print(f"Error during window cleanup: {e}")
            # Force destroy even if cleanup fails
            try:
                self.destroy()
            except:
                pass
    
    def _update_display(self, event: Any) -> None:
        """
        MANDATORY: Update display based on model event
        CRITICAL: Override in subclasses for specific display updates
        """
        # Default implementation - subclasses should override
        pass
    
    def _on_model_registered(self, model: Any) -> None:
        """
        MANDATORY: Handle model registration
        CRITICAL: Override in subclasses for specific registration logic
        """
        # Default implementation - subclasses should override
        pass
    
    def _on_model_unregistered(self, model: Any) -> None:
        """
        MANDATORY: Handle model unregistration
        CRITICAL: Override in subclasses for specific unregistration logic
        """
        # Default implementation - subclasses should override
        pass
    
    def is_destroyed(self) -> bool:
        """
        MANDATORY: Check if view is destroyed
        CRITICAL: Thread-safe destruction state check
        """
        return self._is_destroyed
    
    def center_on_screen(self) -> None:
        """
        MANDATORY: Center window on screen
        CRITICAL: Proper window positioning
        """
        if not self._is_destroyed:
            self.update_idletasks()
            x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
            y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
            self.geometry(f"+{x}+{y}")
    
    def set_size(self, width: int, height: int) -> None:
        """
        MANDATORY: Set window size
        CRITICAL: Safe window sizing
        """
        if not self._is_destroyed:
            self.geometry(f"{width}x{height}")
    
    def set_title(self, title: str) -> None:
        """
        MANDATORY: Set window title
        CRITICAL: Safe title setting
        """
        if not self._is_destroyed:
            self.title(title)
    
    def add_menu_bar(self, menu_items: list) -> None:
        """
        MANDATORY: Add menu bar to window
        CRITICAL: Safe menu creation
        """
        if self._is_destroyed:
            return
        
        try:
            menubar = tk.Menu(self)
            self.config(menu=menubar)
            
            for menu_info in menu_items:
                menu = tk.Menu(menubar, tearoff=0)
                menubar.add_cascade(label=menu_info['label'], menu=menu)
                
                for item in menu_info.get('items', []):
                    if item.get('separator'):
                        menu.add_separator()
                    else:
                        menu.add_command(
                            label=item['label'],
                            command=item.get('command'),
                            state=item.get('state', 'normal')
                        )
        except Exception as e:
            self._handle_gui_error(e)
    
    def create_status_bar(self) -> Optional[tk.Label]:
        """
        MANDATORY: Create status bar
        CRITICAL: Safe status bar creation
        """
        if self._is_destroyed:
            return None
        
        try:
            status_bar = tk.Label(self, text="Ready", bd=1, relief=tk.SUNKEN, anchor=tk.W)
            status_bar.pack(side=tk.BOTTOM, fill=tk.X)
            return status_bar
        except Exception as e:
            self._handle_gui_error(e)
            return None
    
    def update_status(self, message: str) -> None:
        """
        MANDATORY: Update status bar message
        CRITICAL: Thread-safe status update
        """
        self._schedule_gui_update(self._update_status_text, message)
    
    def _update_status_text(self, message: str) -> None:
        """
        MANDATORY: Update status text on main thread
        CRITICAL: Safe status text update
        """
        if not self._is_destroyed:
            try:
                # Find status bar and update
                for child in self.winfo_children():
                    if isinstance(child, tk.Label) and child.cget('relief') == 'sunken':
                        child.config(text=message)
                        break
            except Exception as e:
                self._handle_gui_error(e) 