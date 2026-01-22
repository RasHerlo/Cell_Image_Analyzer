"""
Input Workspace - For loading and managing input images/data.
Organized with tabs for different input-related functions.
"""

from PyQt6.QtWidgets import QTabWidget
from PyQt6.QtCore import Qt

from .base_workspace import BaseWorkspace
from .input_tabs import FileImportTab, GroupsTab
from ...utils.constants import WorkspaceID, Colors


class InputWorkspace(BaseWorkspace):
    """
    Workspace for handling input operations.
    
    Uses a tabbed interface to organize different input functions:
    - File Import: Select and import image files
    - Groups: Organize files into groups based on naming patterns
    """
    
    @property
    def workspace_id(self) -> str:
        return WorkspaceID.INPUT
    
    @property
    def workspace_title(self) -> str:
        return "Input"
    
    def _init_ui(self):
        """Initialize the Input workspace UI with tabs."""
        # Remove default margins since tabs will handle spacing
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background-color: {Colors.BACKGROUND};
            }}
            QTabBar::tab {{
                background-color: {Colors.SECONDARY};
                color: {Colors.TEXT_LIGHT};
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }}
            QTabBar::tab:selected {{
                background-color: {Colors.ACTIVE};
                color: {Colors.TEXT_LIGHT};
            }}
            QTabBar::tab:hover:!selected {{
                background-color: {Colors.HOVER};
            }}
        """)
        
        # Create and add tabs
        self._create_tabs()
        
        # Connect signals
        self._connect_tab_signals()
        
        # Add tab widget to layout
        self.main_layout.addWidget(self.tab_widget)
        
        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
    
    def _create_tabs(self):
        """Create and add all tabs to the tab widget."""
        # File Import tab
        self.file_import_tab = FileImportTab()
        self.tab_widget.addTab(self.file_import_tab, self.file_import_tab.tab_name)
        
        # Groups tab
        self.groups_tab = GroupsTab()
        self.tab_widget.addTab(self.groups_tab, self.groups_tab.tab_name)
    
    def _connect_tab_signals(self):
        """Connect signals between tabs for data flow."""
        # When file selection changes in Import tab, update Groups tab
        self.file_import_tab.files_selected.connect(self._on_files_selected)
    
    def _on_files_selected(self, files: list[str]):
        """
        Handle file selection changes from Import tab.
        
        Args:
            files: List of selected file paths.
        """
        # Update the Groups tab with the new file selection
        self.groups_tab.set_selected_files(files)
    
    def _on_tab_changed(self, index: int):
        """Handle tab change events."""
        # Notify the previous tab that it's being deselected
        for i in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(i)
            if hasattr(tab, 'on_tab_deselected') and i != index:
                tab.on_tab_deselected()
        
        # Notify the new tab that it's being selected
        current_tab = self.tab_widget.widget(index)
        if hasattr(current_tab, 'on_tab_selected'):
            current_tab.on_tab_selected()
        
        # If switching to Groups tab, ensure it has latest file selection
        if current_tab == self.groups_tab:
            selected_files = self.file_import_tab.get_selected_files()
            self.groups_tab.set_selected_files(selected_files)
    
    def on_activated(self):
        """Called when Input workspace becomes active."""
        # Notify current tab
        current_tab = self.tab_widget.currentWidget()
        if hasattr(current_tab, 'on_tab_selected'):
            current_tab.on_tab_selected()
    
    def get_selected_files(self) -> list[str]:
        """
        Get the list of selected files from the File Import tab.
        
        Returns:
            list[str]: List of selected file paths.
        """
        return self.file_import_tab.get_selected_files()
    
    def get_grouped_files(self) -> dict[str, list[str]]:
        """
        Get the files organized into groups from the Groups tab.
        
        Returns:
            dict: Mapping of group keys to lists of file paths.
        """
        return self.groups_tab.get_grouped_files()
