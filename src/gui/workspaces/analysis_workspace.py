"""
Analysis Workspace - For managing analysis data and running analysis pipelines.
Organized with tabs for different analysis-related functions.
"""

from typing import Callable

from PyQt6.QtWidgets import QTabWidget
from PyQt6.QtCore import Qt

from .base_workspace import BaseWorkspace
from .analysis_tabs import PickleDataFileTab, RawProcessingTab
from ...utils.constants import WorkspaceID, Colors


class AnalysisWorkspace(BaseWorkspace):
    """
    Workspace for handling analysis operations.
    
    Uses a tabbed interface to organize different analysis functions:
    - Pickle DataFile: Create, load, and manage pickle data files
    - Raw Processing: Analyze raw image data and generate previews
    """
    
    @property
    def workspace_id(self) -> str:
        return WorkspaceID.ANALYSIS
    
    @property
    def workspace_title(self) -> str:
        return "Analysis"
    
    def _init_ui(self):
        """Initialize the Analysis workspace UI with tabs."""
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
        
        # Set up inter-tab communication
        self._setup_tab_communication()
        
        # Add tab widget to layout
        self.main_layout.addWidget(self.tab_widget)
        
        # Connect tab change signal
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
    
    def _create_tabs(self):
        """Create and add all tabs to the tab widget."""
        # Pickle DataFile tab
        self.pickle_datafile_tab = PickleDataFileTab()
        self.tab_widget.addTab(self.pickle_datafile_tab, self.pickle_datafile_tab.tab_name)
        
        # Raw Processing tab
        self.raw_processing_tab = RawProcessingTab()
        self.tab_widget.addTab(self.raw_processing_tab, self.raw_processing_tab.tab_name)
    
    def _setup_tab_communication(self):
        """Set up communication between tabs."""
        # Raw Processing tab needs access to pickle DataFrame
        self.raw_processing_tab.set_pickle_data_callback(self.get_dataframe)
        
        # Raw Processing tab needs to save modified DataFrame
        self.raw_processing_tab.set_save_pickle_callback(self._update_dataframe)
        
        # Raw Processing tab needs to get pickle file path
        self.raw_processing_tab.set_pickle_path_callback(self.get_pickle_path)
        
        # When pickle file is loaded/created, refresh Raw Processing file list
        self.pickle_datafile_tab.pickle_loaded.connect(
            lambda _: self.raw_processing_tab.refresh_file_list()
        )
    
    def set_input_data_callback(self, callback: Callable):
        """
        Set the callback function to get data from Input workspace.
        
        This allows the Analysis workspace to access selected files
        and grouping information from the Input workspace.
        
        Args:
            callback: Function that returns dict with input data
        """
        self.pickle_datafile_tab.set_input_data_callback(callback)
    
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
    
    def on_activated(self):
        """Called when Analysis workspace becomes active."""
        # Notify current tab
        current_tab = self.tab_widget.currentWidget()
        if hasattr(current_tab, 'on_tab_selected'):
            current_tab.on_tab_selected()
    
    def get_dataframe(self):
        """
        Get the current DataFrame from the Pickle DataFile tab.
        
        Returns:
            The current DataFrame or None.
        """
        return self.pickle_datafile_tab.get_dataframe()
    
    def get_pickle_path(self) -> str | None:
        """
        Get the current pickle file path.
        
        Returns:
            The file path or None.
        """
        return self.pickle_datafile_tab.get_pickle_path()
    
    def _update_dataframe(self, df: 'pd.DataFrame', filepath: str):
        """
        Update the DataFrame in the Pickle DataFile tab.
        
        This is called when another tab modifies the DataFrame and saves it.
        
        Args:
            df: The updated DataFrame.
            filepath: The path where the DataFrame was saved.
        """
        self.pickle_datafile_tab.update_dataframe(df, filepath)
    
    def load_pickle_file(self, filepath: str):
        """
        Load a pickle file from an external path.
        
        This is called when a pickle file is selected from another workspace
        (e.g., Output workspace).
        
        Args:
            filepath: Path to the pickle file to load.
        """
        self.pickle_datafile_tab.load_pickle_from_path(filepath)
