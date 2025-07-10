#!/usr/bin/env python3
"""
MANDATORY: Test suite for View Base Classes
CRITICAL: Tests thread safety, MVC integration, and proper cleanup
"""

import unittest
import tkinter as tk
import threading
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Any
import weakref

# Import our view components
from view import View, ModelListener, ViewFactory
from tkinter_view import TkinterView


class MockModel:
    """Mock model for testing observer pattern"""
    
    def __init__(self):
        self.observers = []
        self.data = "initial"
    
    def add_observer(self, observer):
        """Add observer to model"""
        if observer not in self.observers:
            self.observers.append(observer)
            observer.model_registered(self)
    
    def remove_observer(self, observer):
        """Remove observer from model"""
        if observer in self.observers:
            self.observers.remove(observer)
            observer.model_unregistered(self)
    
    def notify_observers(self, event):
        """Notify all observers of model change"""
        for observer in self.observers[:]:  # Copy list to avoid modification during iteration
            observer.model_changed(event)
    
    def update_data(self, new_data):
        """Update model data and notify observers"""
        self.data = new_data
        self.notify_observers({"type": "data_update", "data": new_data})


class MockController:
    """Mock controller for testing MVC integration"""
    
    def __init__(self):
        self.view = None
        self.model = None
    
    def set_view(self, view):
        """Set view reference"""
        self.view = view
    
    def set_model(self, model):
        """Set model reference"""
        self.model = model
    
    def get_model(self):
        """Get model reference"""
        return self.model


class TestViewInterface(unittest.TestCase):
    """Test View interface functionality"""
    
    def setUp(self):
        """Setup test environment"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide window during tests
    
    def tearDown(self):
        """Cleanup test environment"""
        try:
            self.root.destroy()
        except:
            pass
    
    def test_view_interface_abstract(self):
        """Test that View is abstract and cannot be instantiated"""
        with self.assertRaises(TypeError):
            View()
    
    def test_model_listener_interface_abstract(self):
        """Test that ModelListener is abstract and cannot be instantiated"""
        with self.assertRaises(TypeError):
            ModelListener()
    
    def test_view_factory_interface_abstract(self):
        """Test that ViewFactory is abstract and cannot be instantiated"""
        with self.assertRaises(TypeError):
            ViewFactory()


class TestTkinterView(unittest.TestCase):
    """Test TkinterView base class functionality"""
    
    def setUp(self):
        """Setup test environment"""
        self.root = tk.Tk()
        self.root.withdraw()
    
    def tearDown(self):
        """Cleanup test environment"""
        try:
            self.root.destroy()
        except:
            pass
    
    def test_tkinter_view_creation(self):
        """Test TkinterView creation and basic functionality"""
        view = TkinterView(title="Test View")
        self.assertIsInstance(view, tk.Toplevel)
        self.assertIsInstance(view, View)
        self.assertIsInstance(view, ModelListener)
        self.assertEqual(view.title(), "Test View")
        self.assertFalse(view.is_destroyed())
        view.destroy()
    
    def test_tkinter_view_controller_assignment(self):
        """Test controller assignment and retrieval"""
        view = TkinterView()
        controller = MockController()
        
        # Test setting controller
        view.set_controller(controller)
        self.assertEqual(view.get_controller(), controller)
        
        # Test setting None
        view.set_controller(None)
        self.assertIsNone(view.get_controller())
        
        view.destroy()
    
    def test_tkinter_view_model_assignment(self):
        """Test model assignment with observer pattern"""
        view = TkinterView()
        model = MockModel()
        
        # Test setting model
        view.set_model(model)
        self.assertEqual(view.get_model(), model)
        
        # Verify observer registration
        self.assertIn(view, model.observers)
        
        # Test setting None
        view.set_model(None)
        self.assertIsNone(view.get_model())
        
        # Verify observer unregistration
        self.assertNotIn(view, model.observers)
        
        view.destroy()
    
    def test_tkinter_view_model_change_handling(self):
        """Test model change event handling"""
        view = TkinterView()
        model = MockModel()
        view.set_model(model)
        
        # Track if model_changed was called
        model_changed_called = threading.Event()
        
        def mock_model_changed(event):
            model_changed_called.set()
        
        # Override model_changed method
        view.model_changed = mock_model_changed
        
        # Trigger model change
        model.update_data("new data")
        
        # Wait for model_changed to be called
        time.sleep(0.1)
        self.assertTrue(model_changed_called.is_set())
        
        view.destroy()
    
    def test_tkinter_view_thread_safety(self):
        """Test thread-safe GUI updates"""
        view = TkinterView()
        update_called = threading.Event()
        
        def test_update():
            update_called.set()
        
        # Schedule update from different thread
        def schedule_from_thread():
            view._schedule_gui_update(test_update)
        
        thread = threading.Thread(target=schedule_from_thread)
        thread.start()
        thread.join()
        
        # Wait for update to be called
        time.sleep(0.1)
        self.assertTrue(update_called.is_set())
        
        view.destroy()
    
    def test_tkinter_view_error_handling(self):
        """Test error handling in GUI operations"""
        view = TkinterView()
        
        with patch('tkinter.messagebox.showerror') as mock_error:
            # Test show_error
            view.show_error("Test error")
            time.sleep(0.1)
            mock_error.assert_called_with("Error", "Test error")
        
        with patch('tkinter.messagebox.showinfo') as mock_info:
            # Test show_info
            view.show_info("Test info")
            time.sleep(0.1)
            mock_info.assert_called_with("Information", "Test info")
        
        view.destroy()
    
    def test_tkinter_view_window_lifecycle(self):
        """Test window lifecycle management"""
        view = TkinterView()
        model = MockModel()
        controller = MockController()
        
        # Setup MVC relationships
        view.set_model(model)
        view.set_controller(controller)
        
        # Verify initial state
        self.assertFalse(view.is_destroyed())
        self.assertIn(view, model.observers)
        self.assertEqual(controller.view, None)  # Controller doesn't auto-set view
        
        # Test window closing
        view.on_closing()
        
        # Verify cleanup
        self.assertTrue(view.is_destroyed())
        self.assertNotIn(view, model.observers)
        self.assertIsNone(view.get_model())
        self.assertIsNone(view.get_controller())
    
    def test_tkinter_view_window_properties(self):
        """Test window property management"""
        view = TkinterView(title="Original Title")
        
        # Test title setting
        view.set_title("New Title")
        self.assertEqual(view.title(), "New Title")
        
        # Test size setting
        view.set_size(800, 600)
        self.assertEqual(view.winfo_width(), 800)
        self.assertEqual(view.winfo_height(), 600)
        
        # Test centering
        view.center_on_screen()
        
        view.destroy()
    
    def test_tkinter_view_menu_bar(self):
        """Test menu bar creation"""
        view = TkinterView()
        
        menu_items = [
            {
                'label': 'File',
                'items': [
                    {'label': 'New', 'command': lambda: None},
                    {'label': 'Open', 'command': lambda: None},
                    {'separator': True},
                    {'label': 'Exit', 'command': lambda: None}
                ]
            },
            {
                'label': 'Edit',
                'items': [
                    {'label': 'Cut', 'command': lambda: None},
                    {'label': 'Copy', 'command': lambda: None},
                    {'label': 'Paste', 'command': lambda: None}
                ]
            }
        ]
        
        view.add_menu_bar(menu_items)
        
        # Verify menu bar was created
        self.assertIsNotNone(view.cget('menu'))
        
        view.destroy()
    
    def test_tkinter_view_status_bar(self):
        """Test status bar creation and updates"""
        view = TkinterView()
        
        # Create status bar
        status_bar = view.create_status_bar()
        self.assertIsNotNone(status_bar)
        
        # Test status update
        view.update_status("Processing...")
        time.sleep(0.1)
        
        # Verify status was updated
        self.assertEqual(status_bar.cget('text'), "Processing...")
        
        view.destroy()
    
    def test_tkinter_view_concurrent_access(self):
        """Test concurrent access to view properties"""
        view = TkinterView()
        model = MockModel()
        controller = MockController()
        
        # Setup MVC relationships
        view.set_model(model)
        view.set_controller(controller)
        
        # Test concurrent property access
        def access_properties():
            for _ in range(100):
                view.get_model()
                view.get_controller()
                view.is_valid()
        
        # Start multiple threads
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=access_properties)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify no exceptions occurred
        self.assertTrue(view.is_valid())
        
        view.destroy()
    
    def test_tkinter_view_memory_management(self):
        """Test memory management and cleanup"""
        view = TkinterView()
        model = MockModel()
        controller = MockController()
        
        # Setup MVC relationships
        view.set_model(model)
        view.set_controller(controller)
        
        # Create weak reference to track garbage collection
        weak_view = weakref.ref(view)
        
        # Close window
        view.on_closing()
        
        # Force garbage collection
        import gc
        gc.collect()
        
        # Verify view was properly cleaned up
        self.assertIsNone(weak_view())
    
    def test_tkinter_view_destroyed_state(self):
        """Test behavior when view is destroyed"""
        view = TkinterView()
        
        # Destroy view
        view.on_closing()
        
        # Verify destroyed state
        self.assertTrue(view.is_destroyed())
        
        # Test operations on destroyed view
        view.set_title("Should not work")
        view.set_size(100, 100)
        view.center_on_screen()
        view.show_error("Should not work")
        view.show_info("Should not work")
        
        # These operations should not raise exceptions but should be ignored
        # since the view is destroyed


class TestViewIntegration(unittest.TestCase):
    """Test integration between View components"""
    
    def setUp(self):
        """Setup test environment"""
        self.root = tk.Tk()
        self.root.withdraw()
    
    def tearDown(self):
        """Cleanup test environment"""
        try:
            self.root.destroy()
        except:
            pass
    
    def test_mvc_integration(self):
        """Test complete MVC integration"""
        # Create MVC components
        model = MockModel()
        controller = MockController()
        view = TkinterView()
        
        # Setup MVC relationships
        controller.set_model(model)
        view.set_controller(controller)
        view.set_model(model)
        
        # Verify MVC relationships
        self.assertEqual(view.get_model(), model)
        self.assertEqual(view.get_controller(), controller)
        self.assertEqual(controller.get_model(), model)
        self.assertTrue(view.is_valid())
        
        # Test model change propagation
        update_received = threading.Event()
        
        def on_model_change(event):
            update_received.set()
        
        view._update_display = on_model_change
        
        # Trigger model change
        model.update_data("test data")
        
        # Wait for update
        time.sleep(0.1)
        self.assertTrue(update_received.is_set())
        
        # Cleanup
        view.on_closing()
    
    def test_multiple_views_same_model(self):
        """Test multiple views observing the same model"""
        model = MockModel()
        view1 = TkinterView(title="View 1")
        view2 = TkinterView(title="View 2")
        
        # Register both views with model
        view1.set_model(model)
        view2.set_model(model)
        
        # Verify both views are registered
        self.assertIn(view1, model.observers)
        self.assertIn(view2, model.observers)
        
        # Track updates
        view1_updated = threading.Event()
        view2_updated = threading.Event()
        
        def on_view1_update(event):
            view1_updated.set()
        
        def on_view2_update(event):
            view2_updated.set()
        
        view1._update_display = on_view1_update
        view2._update_display = on_view2_update
        
        # Trigger model change
        model.update_data("shared data")
        
        # Wait for updates
        time.sleep(0.1)
        self.assertTrue(view1_updated.is_set())
        self.assertTrue(view2_updated.is_set())
        
        # Cleanup
        view1.on_closing()
        view2.on_closing()
    
    def test_view_controller_communication(self):
        """Test communication between view and controller"""
        model = MockModel()
        controller = MockController()
        view = TkinterView()
        
        # Setup MVC relationships
        controller.set_model(model)
        view.set_controller(controller)
        view.set_model(model)
        
        # Test view can access controller
        self.assertEqual(view.get_controller(), controller)
        
        # Test view can access model through controller
        self.assertEqual(controller.get_model(), model)
        
        # Test cleanup clears relationships
        view.on_closing()
        self.assertIsNone(view.get_controller())
        self.assertIsNone(view.get_model())


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2) 