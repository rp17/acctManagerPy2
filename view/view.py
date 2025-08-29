"""
MANDATORY: View Interface - Abstract base class for all views
CRITICAL: Defines view contract with MVC architecture preservation
"""

from abc import ABC, abstractmethod
from typing import Optional, Any
from threading import Lock


class View(ABC):
    """
    MANDATORY: Abstract base class defining view contract
    CRITICAL: Ensures exact MVC architecture preservation from Java implementation
    """
    
    def __init__(self):
        """Initialize view with thread-safe property access"""
        self._controller: Optional[Any] = None
        self._model: Optional[Any] = None
        self._lock = Lock()  # CRITICAL: Thread-safe property access
    
    @abstractmethod
    def get_controller(self) -> Optional[Any]:
        """
        MANDATORY: Get controller reference
        CRITICAL: Thread-safe property access
        """
        with self._lock:
            return self._controller
    
    @abstractmethod
    def set_controller(self, controller: Optional[Any]) -> None:
        """
        MANDATORY: Set controller reference
        CRITICAL: Thread-safe property access
        """
        with self._lock:
            self._controller = controller
    
    @abstractmethod
    def get_model(self) -> Optional[Any]:
        """
        MANDATORY: Get model reference
        CRITICAL: Thread-safe property access
        """
        with self._lock:
            return self._model
    
    @abstractmethod
    def set_model(self, model: Optional[Any]) -> None:
        """
        MANDATORY: Set model reference
        CRITICAL: Thread-safe property access with observer pattern
        """
        with self._lock:
            # Unregister from previous model if exists
            if self._model is not None:
                self._unregister_with_model()
            
            self._model = model
            
            # Register with new model if exists
            if self._model is not None:
                self._register_with_model()
    
    @abstractmethod
    def model_changed(self, event: Any) -> None:
        """
        MANDATORY: Handle model change events
        CRITICAL: Observer pattern implementation for model-view synchronization
        """
        pass
    
    @abstractmethod
    def show_error(self, message: str) -> None:
        """
        MANDATORY: Display error message to user
        CRITICAL: Thread-safe error display
        """
        pass
    
    @abstractmethod
    def show_info(self, message: str) -> None:
        """
        MANDATORY: Display info message to user
        CRITICAL: Thread-safe info display
        """
        pass
    
    @abstractmethod
    def on_closing(self) -> None:
        """
        MANDATORY: Handle window closing event
        CRITICAL: Proper cleanup and resource deallocation
        """
        pass
    
    def _register_with_model(self) -> None:
        """
        CRITICAL: Register with model using observer pattern
        MANDATORY: Implementation depends on model interface
        """
        if self._model is not None and hasattr(self._model, 'add_observer'):
            self._model.add_observer(self)
    
    def _unregister_with_model(self) -> None:
        """
        CRITICAL: Unregister from model using observer pattern
        MANDATORY: Implementation depends on model interface
        """
        if self._model is not None and hasattr(self._model, 'remove_observer'):
            self._model.remove_observer(self)
    
    def _cleanup_resources(self) -> None:
        """
        MANDATORY: Cleanup resources and prevent memory leaks
        CRITICAL: Clear references and unregister from model
        """
        with self._lock:
            # Unregister from model
            self._unregister_with_model()
            
            # Clear controller reference
            if self._controller is not None:
                if hasattr(self._controller, 'set_view'):
                    self._controller.set_view(None)
                self._controller = None
            
            # Clear model reference
            self._model = None
    
    def is_valid(self) -> bool:
        """
        MANDATORY: Check if view is in valid state
        CRITICAL: Thread-safe validation check
        """
        with self._lock:
            return self._controller is not None and self._model is not None
    
    def get_view_info(self) -> dict:
        """
        MANDATORY: Get view information for debugging
        CRITICAL: Thread-safe information retrieval
        """
        with self._lock:
            return {
                'controller': type(self._controller).__name__ if self._controller else None,
                'model': type(self._model).__name__ if self._model else None,
                'valid': self.is_valid()
            }


class ModelListener(ABC):
    """
    MANDATORY: Model listener interface for observer pattern
    CRITICAL: Defines contract for model change notifications
    """
    
    @abstractmethod
    def model_changed(self, event: Any) -> None:
        """
        MANDATORY: Handle model change events
        CRITICAL: Called when model state changes
        """
        pass
    
    @abstractmethod
    def model_registered(self, model: Any) -> None:
        """
        MANDATORY: Handle model registration
        CRITICAL: Called when view is registered with model
        """
        pass
    
    @abstractmethod
    def model_unregistered(self, model: Any) -> None:
        """
        MANDATORY: Handle model unregistration
        CRITICAL: Called when view is unregistered from model
        """
        pass


class ViewFactory(ABC):
    """
    MANDATORY: View factory interface for view creation
    CRITICAL: Ensures consistent view instantiation
    """
    
    @abstractmethod
    def create_view(self, view_type: str, **kwargs) -> View:
        """
        MANDATORY: Create view instance
        CRITICAL: Factory method for view creation
        """
        pass
    
    @abstractmethod
    def register_view_type(self, view_type: str, view_class: type) -> None:
        """
        MANDATORY: Register view type with factory
        CRITICAL: Allow dynamic view type registration
        """
        pass 