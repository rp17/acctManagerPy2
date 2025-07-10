import tkinter as tk
from tkinter import ttk, messagebox
from decimal import Decimal
from typing import Any, Optional
from abc import ABC, abstractmethod
from account_model import ModelEvent, EventKind


class View(ABC):
    """MANDATORY: Base view interface"""
    
    @abstractmethod
    def set_controller(self, controller: Any) -> None:
        """Set the controller reference"""
        pass
    
    @abstractmethod
    def update_from_model(self, event: ModelEvent) -> None:
        """Handle model update events"""
        pass
    
    @abstractmethod
    def show_error(self, message: str) -> None:
        """Display error message to user"""
        pass


class FrameView(ttk.Frame, View):
    """
    MANDATORY: Base frame view with thread-safe updates
    CRITICAL: Provides common functionality for all views
    """
    
    def __init__(self, parent: tk.Misc, **kwargs):
        super().__init__(parent, **kwargs)
        self._controller: Optional[Any] = None
        self._setup_style()
    
    def _setup_style(self) -> None:
        """Setup modern ttk styling"""
        try:
            style = ttk.Style()
            style.theme_use("clam")
            
            # Configure common styles
            style.configure("Title.TLabel", font=("Segoe UI", 14, "bold"))
            style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"))
            style.configure("Status.TLabel", font=("Segoe UI", 10))
            style.configure("Action.TButton", font=("Segoe UI", 10, "bold"))
            
        except tk.TclError:
            # Fallback if clam theme is not available
            pass
    
    def set_controller(self, controller: Any) -> None:
        """CRITICAL: Thread-safe controller assignment"""
        self._controller = controller
    
    def get_controller(self) -> Optional[Any]:
        """Get current controller"""
        return self._controller
    
    def update_from_model(self, event: ModelEvent) -> None:
        """
        MANDATORY: Thread-safe model update handling
        CRITICAL: Uses after(0, ...) for thread safety
        """
        # Default implementation - subclasses should override
        pass
    
    def show_error(self, message: str) -> None:
        """
        CRITICAL: Thread-safe error display
        MANDATORY: Uses after(0, ...) for thread safety
        """
        self.after(0, lambda: messagebox.showerror("Error", message))
    
    def show_info(self, message: str) -> None:
        """Thread-safe info message display"""
        self.after(0, lambda: messagebox.showinfo("Information", message))
    
    def show_warning(self, message: str) -> None:
        """Thread-safe warning message display"""
        self.after(0, lambda: messagebox.showwarning("Warning", message))
    
    def ask_yes_no(self, message: str, title: str = "Confirm") -> bool:
        """Thread-safe yes/no dialog"""
        return bool(messagebox.askyesno(title, message))
    
    def schedule_update(self, callback: callable, *args, **kwargs) -> None:
        """
        CRITICAL: Schedule thread-safe GUI update
        MANDATORY: Use this for all GUI updates from non-GUI threads
        """
        self.after(0, lambda: callback(*args, **kwargs))
    
    def on_close(self) -> None:
        """Handle window close event"""
        if self._controller is not None:
            # Notify controller for cleanup
            if hasattr(self._controller, 'on_view_closing'):
                self._controller.on_view_closing()
    
    def configure_grid_weights(self, rows: list, cols: list) -> None:
        """
        CRITICAL: Configure grid weights for responsive layout
        MANDATORY: Use for consistent spacing and resizing
        """
        for i, weight in enumerate(rows):
            self.grid_rowconfigure(i, weight=weight)
        for i, weight in enumerate(cols):
            self.grid_columnconfigure(i, weight=weight)


class DialogView(tk.Toplevel, View):
    """
    MANDATORY: Base dialog view with thread-safe updates
    CRITICAL: Provides modal dialog functionality
    """
    
    def __init__(self, parent: tk.Misc, title: str = "Dialog", **kwargs):
        super().__init__(parent, **kwargs)
        self.title(title)
        self._controller: Optional[Any] = None
        self._setup_dialog()
        self._setup_style()
    
    def _setup_dialog(self) -> None:
        """Setup dialog properties"""
        if hasattr(self.master, 'wm_transient'):
            self.transient(self.master)
        self.grab_set()
        self.resizable(False, False)
        
        # Center dialog on parent
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        # Handle close event
        self.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def _setup_style(self) -> None:
        """Setup modern ttk styling"""
        try:
            style = ttk.Style()
            style.theme_use("clam")
        except tk.TclError:
            pass
    
    def set_controller(self, controller: Any) -> None:
        """CRITICAL: Thread-safe controller assignment"""
        self._controller = controller
    
    def get_controller(self) -> Optional[Any]:
        """Get current controller"""
        return self._controller
    
    def update_from_model(self, event: ModelEvent) -> None:
        """
        MANDATORY: Thread-safe model update handling
        CRITICAL: Uses after(0, ...) for thread safety
        """
        # Default implementation - subclasses should override
        pass
    
    def show_error(self, message: str) -> None:
        """
        CRITICAL: Thread-safe error display
        MANDATORY: Uses after(0, ...) for thread safety
        """
        self.after(0, lambda: messagebox.showerror("Error", message))
    
    def schedule_update(self, callback: callable, *args, **kwargs) -> None:
        """
        CRITICAL: Schedule thread-safe GUI update
        MANDATORY: Use this for all GUI updates from non-GUI threads
        """
        self.after(0, lambda: callback(*args, **kwargs))
    
    def on_close(self) -> None:
        """Handle dialog close event"""
        if self._controller is not None:
            # Notify controller for cleanup
            if hasattr(self._controller, 'on_view_closing'):
                self._controller.on_view_closing()
        self.destroy()
    
    def center_on_parent(self) -> None:
        """Center dialog on parent window"""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")


class SpringUtilities:
    """
    CRITICAL: Utility class for consistent grid layout
    MANDATORY: Provides grid_configure helper for spacing
    """
    
    @staticmethod
    def make_grid(parent: tk.Misc, rows: int, cols: int) -> None:
        """Configure grid weights for responsive layout"""
        for i in range(rows):
            parent.grid_rowconfigure(i, weight=1)
        for i in range(cols):
            parent.grid_columnconfigure(i, weight=1)
    
    @staticmethod
    def make_compact_grid(parent: tk.Misc, rows: int, cols: int) -> None:
        """Configure grid weights for compact layout"""
        for i in range(rows):
            parent.grid_rowconfigure(i, weight=0)
        for i in range(cols):
            parent.grid_columnconfigure(i, weight=1)
    
    @staticmethod
    def add_padding(widget: tk.Misc, padx: int = 4, pady: int = 4) -> None:
        """Add consistent padding to widget"""
        # Note: Not all widgets support padx/pady in configure
        pass
    
    @staticmethod
    def create_separator(parent: tk.Misc, orient: str = "horizontal") -> ttk.Separator:
        """Create a styled separator"""
        if orient == "horizontal":
            return ttk.Separator(parent, orient="horizontal")
        else:
            return ttk.Separator(parent, orient="vertical")
    
    @staticmethod
    def create_title_label(parent: tk.Misc, text: str) -> ttk.Label:
        """Create a styled title label"""
        return ttk.Label(parent, text=text, style="Title.TLabel")
    
    @staticmethod
    def create_header_label(parent: tk.Misc, text: str) -> ttk.Label:
        """Create a styled header label"""
        return ttk.Label(parent, text=text, style="Header.TLabel")
    
    @staticmethod
    def create_action_button(parent: tk.Misc, text: str, command: callable) -> ttk.Button:
        """Create a styled action button"""
        return ttk.Button(parent, text=text, command=command, style="Action.TButton") 