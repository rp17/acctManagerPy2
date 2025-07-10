#!/usr/bin/env python3
"""
MANDATORY: Main application for Account Manager MVC System
CRITICAL: Demonstrates complete MVC architecture with Tkinter GUI
"""

import tkinter as tk
from tkinter import ttk
import sys
import signal
from decimal import Decimal

# Import our MVC components
from mvc_controller import MainController
from view.account_list_view import AccountListView
from agent_system import AgentImpl


class AccountManagerApp:
    """
    MANDATORY: Main application class
    CRITICAL: Coordinates MVC components and handles application lifecycle
    """
    
    def __init__(self):
        """Initialize the application"""
        self.root = None
        self.main_controller = None
        self.main_view = None
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        self.shutdown()
        sys.exit(0)
    
    def setup_gui(self):
        """Setup the Tkinter GUI"""
        # Create root window
        self.root = tk.Tk()
        self.root.title("Account Manager - MVC System")
        self.root.geometry("800x600")
        
        # Configure window close handler
        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)
        
        # Setup modern styling
        self._setup_styling()
        
        # Create main controller
        self.main_controller = MainController()
        
        # Create main view
        self.main_view = AccountListView(self.root, self.main_controller)
        self.main_view.pack(fill="both", expand=True, padx=8, pady=8)
        
        # Initialize default accounts
        self._initialize_default_accounts()
        
        # Setup periodic updates
        self._setup_periodic_updates()
    
    def _setup_styling(self):
        """Setup modern ttk styling"""
        try:
            style = ttk.Style()
            style.theme_use("clam")
            
            # Configure custom styles
            style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"))
            style.configure("Header.TLabel", font=("Segoe UI", 12, "bold"))
            style.configure("Status.TLabel", font=("Segoe UI", 10))
            style.configure("Action.TButton", font=("Segoe UI", 10, "bold"))
            
        except tk.TclError:
            # Fallback if clam theme is not available
            pass
    
    def _initialize_default_accounts(self):
        """Initialize default accounts for demonstration"""
        try:
            self.main_controller.initialize_default_accounts()
            print("Default accounts initialized successfully")
        except Exception as e:
            print(f"Warning: Failed to initialize default accounts: {e}")
    
    def _setup_periodic_updates(self):
        """Setup periodic GUI updates"""
        def update_display():
            try:
                # Refresh all account views
                if self.main_view:
                    self.main_view.refresh_all_accounts()
                
                # Schedule next update
                self.root.after(1000, update_display)  # Update every second
                
            except Exception as e:
                print(f"Error in periodic update: {e}")
        
        # Start periodic updates
        self.root.after(1000, update_display)
    
    def run(self):
        """Run the application"""
        try:
            print("Starting Account Manager MVC System...")
            print("Features:")
            print("- Thread-safe account operations")
            print("- Automated deposit/withdrawal agents")
            print("- Real-time balance updates")
            print("- Concurrent testing capabilities")
            print("- Modern Tkinter GUI")
            print("\nPress Ctrl+C to exit gracefully\n")
            
            # Start the GUI event loop
            self.root.mainloop()
            
        except Exception as e:
            print(f"Error running application: {e}")
            self.shutdown()
    
    def shutdown(self):
        """Graceful shutdown of the application"""
        try:
            print("Shutting down Account Manager...")
            
            # Shutdown main controller
            if self.main_controller:
                self.main_controller.shutdown()
            
            # Shutdown thread pool
            AgentImpl.shutdown_executor()
            
            # Destroy GUI
            if self.root:
                self.root.quit()
                self.root.destroy()
            
            print("Shutdown complete")
            
        except Exception as e:
            print(f"Error during shutdown: {e}")


def main():
    """Main entry point"""
    app = AccountManagerApp()
    
    try:
        app.setup_gui()
        app.run()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        app.shutdown()
    except Exception as e:
        print(f"Fatal error: {e}")
        app.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    main() 