"""
Main Window - The primary application window with navigation and workspace container.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QFrame, QStackedWidget
)
from PyQt6.QtCore import Qt

from .components import NavButton
from .workspaces import InputWorkspace, AnalysisWorkspace, OutputWorkspace
from ..utils.constants import (
    APP_NAME, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT,
    NAV_PANEL_WIDTH, WorkspaceID, DEFAULT_WORKSPACE, Colors
)


class MainWindow(QMainWindow):
    """
    The main application window.
    
    Layout:
    - Left side: Navigation panel with vertical buttons
    - Right side: Workspace container (stacked widget)
    """
    
    def __init__(self):
        super().__init__()
        self._nav_buttons: dict[str, NavButton] = {}
        self._workspaces: dict[str, QWidget] = {}
        
        self._setup_window()
        self._init_ui()
        self._connect_signals()
        self._setup_workspace_communication()
        
        # Set default workspace
        self._switch_workspace(DEFAULT_WORKSPACE)
    
    def _setup_window(self):
        """Configure the main window properties."""
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
    
    def _init_ui(self):
        """Initialize the main UI layout."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main horizontal layout
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create navigation panel (left side)
        nav_panel = self._create_nav_panel()
        main_layout.addWidget(nav_panel)
        
        # Create workspace container (right side)
        self.workspace_container = self._create_workspace_container()
        main_layout.addWidget(self.workspace_container, 1)  # stretch factor 1
    
    def _create_nav_panel(self) -> QFrame:
        """
        Create the navigation panel with vertical buttons.
        
        Returns:
            QFrame: The navigation panel widget.
        """
        nav_panel = QFrame()
        nav_panel.setFixedWidth(NAV_PANEL_WIDTH)
        nav_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.PRIMARY};
                border: none;
            }}
        """)
        
        # Vertical layout for buttons
        layout = QVBoxLayout(nav_panel)
        layout.setContentsMargins(10, 20, 10, 20)
        layout.setSpacing(10)
        
        # Create navigation buttons
        button_configs = [
            ("INPUT", WorkspaceID.INPUT),
            ("ANALYSIS", WorkspaceID.ANALYSIS),
            ("OUTPUT", WorkspaceID.OUTPUT),
        ]
        
        for text, workspace_id in button_configs:
            button = NavButton(text, workspace_id)
            self._nav_buttons[workspace_id] = button
            layout.addWidget(button)
        
        # Push buttons to top
        layout.addStretch()
        
        return nav_panel
    
    def _create_workspace_container(self) -> QStackedWidget:
        """
        Create the workspace container with all workspace panels.
        
        Returns:
            QStackedWidget: The stacked widget containing all workspaces.
        """
        container = QStackedWidget()
        container.setStyleSheet(f"""
            QStackedWidget {{
                background-color: {Colors.BACKGROUND};
            }}
        """)
        
        # Create and add workspaces
        workspace_classes = [
            (WorkspaceID.INPUT, InputWorkspace),
            (WorkspaceID.ANALYSIS, AnalysisWorkspace),
            (WorkspaceID.OUTPUT, OutputWorkspace),
        ]
        
        for workspace_id, workspace_class in workspace_classes:
            workspace = workspace_class()
            self._workspaces[workspace_id] = workspace
            container.addWidget(workspace)
        
        return container
    
    def _connect_signals(self):
        """Connect navigation button signals."""
        for button in self._nav_buttons.values():
            button.workspace_selected.connect(self._switch_workspace)
    
    def _setup_workspace_communication(self):
        """Set up communication channels between workspaces."""
        # Get workspace references
        input_workspace: InputWorkspace = self._workspaces.get(WorkspaceID.INPUT)
        analysis_workspace: AnalysisWorkspace = self._workspaces.get(WorkspaceID.ANALYSIS)
        
        # Set up callback for Analysis workspace to get Input data
        if input_workspace and analysis_workspace:
            analysis_workspace.set_input_data_callback(
                self._get_input_workspace_data
            )
    
    def _get_input_workspace_data(self) -> dict:
        """
        Get data from the Input workspace for use by other workspaces.
        
        Returns:
            dict: Contains selected_files, grouped_files, and grouping_enabled
        """
        input_workspace: InputWorkspace = self._workspaces.get(WorkspaceID.INPUT)
        
        if not input_workspace:
            return {
                'selected_files': [],
                'grouped_files': {},
                'grouping_enabled': False
            }
        
        # Get selected files
        selected_files = input_workspace.get_selected_files()
        
        # Get grouped files and check if grouping is enabled
        grouped_files = input_workspace.get_grouped_files()
        
        # Determine if grouping is actually enabled
        # (if there's more than one group and it's not just "all")
        grouping_enabled = (
            len(grouped_files) > 1 or 
            (len(grouped_files) == 1 and "all" not in grouped_files)
        )
        
        return {
            'selected_files': selected_files,
            'grouped_files': grouped_files,
            'grouping_enabled': grouping_enabled
        }
    
    def _switch_workspace(self, workspace_id: str):
        """
        Switch to the specified workspace.
        
        Args:
            workspace_id: The ID of the workspace to switch to.
        """
        # Update button states
        for btn_id, button in self._nav_buttons.items():
            button.set_active(btn_id == workspace_id)
        
        # Get the workspace widgets
        current_workspace = self.workspace_container.currentWidget()
        new_workspace = self._workspaces.get(workspace_id)
        
        if new_workspace is None:
            return
        
        # Notify workspaces of activation/deactivation
        if current_workspace and hasattr(current_workspace, 'on_deactivated'):
            current_workspace.on_deactivated()
        
        if hasattr(new_workspace, 'on_activated'):
            new_workspace.on_activated()
        
        # Switch the visible workspace
        self.workspace_container.setCurrentWidget(new_workspace)
