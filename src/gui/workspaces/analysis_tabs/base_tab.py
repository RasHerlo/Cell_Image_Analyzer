"""
Base Tab class for Analysis workspace tabs.
Provides a consistent interface for all tabs within the Analysis workspace.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import pyqtSignal


class BaseTab(QWidget):
    """
    Base class for all Analysis workspace tabs.
    
    Subclasses should implement:
    - _init_ui(): Initialize the tab UI components
    - tab_name (property): Return the display name for the tab
    """
    
    # Signal emitted when tab data changes
    data_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_base_layout()
        self._init_ui()
    
    def _setup_base_layout(self):
        """Set up the base layout for the tab."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(15, 15, 15, 15)
        self.main_layout.setSpacing(15)
    
    def _init_ui(self):
        """
        Initialize the tab UI components.
        Must be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement _init_ui()")
    
    @property
    def tab_name(self) -> str:
        """
        Return the display name for this tab.
        Must be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement tab_name property")
    
    def on_tab_selected(self):
        """
        Called when this tab becomes the active tab.
        Override in subclasses if needed.
        """
        pass
    
    def on_tab_deselected(self):
        """
        Called when this tab is no longer the active tab.
        Override in subclasses if needed.
        """
        pass
    
    def get_data(self) -> dict:
        """
        Get the current data/state from this tab.
        Override in subclasses to return relevant data.
        
        Returns:
            dict: Tab data that can be used by other components.
        """
        return {}

