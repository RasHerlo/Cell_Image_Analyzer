"""
Output Workspace - For viewing and exporting analysis results.
"""

import os
from typing import Callable

import numpy as np
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QLineEdit, QPushButton, QCheckBox, QGroupBox, QSplitter,
    QScrollArea, QButtonGroup, QFileDialog, QMessageBox,
    QListWidget, QListWidgetItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal

# Matplotlib imports for embedding in PyQt6
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from .base_workspace import BaseWorkspace
from ...utils.constants import WorkspaceID, Colors


class OutputWorkspace(BaseWorkspace):
    """
    Workspace for handling output operations.
    
    This workspace contains:
    - Settings pane with pickle file selection and toggles
    - File overview showing groups
    - Preview pane with sheets for each group
    """
    
    # Signal emitted when a new pickle file is loaded
    pickle_file_changed = pyqtSignal(str)
    
    @property
    def workspace_id(self) -> str:
        return WorkspaceID.OUTPUT
    
    @property
    def workspace_title(self) -> str:
        return "Output"
    
    def _init_ui(self):
        """Initialize the Output workspace UI."""
        # Callbacks
        self._get_pickle_data_callback: Callable | None = None
        self._get_pickle_path_callback: Callable | None = None
        self._load_pickle_file_callback: Callable | None = None
        
        # Current state
        self._dataframe: pd.DataFrame | None = None
        self._current_pickle_path: str | None = None
        self._group_toggles: dict[str, QCheckBox] = {}
        self._current_sheet_index: int = 0
        self._sheets_data: list[dict] = []
        
        # Color palette for files within groups (tab10 colormap)
        self._file_colors = plt.cm.tab10.colors
        
        # Create main layout
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter.setHandleWidth(2)
        
        # Settings pane (top)
        settings_pane = self._create_settings_pane()
        main_splitter.addWidget(settings_pane)
        
        # Content area (bottom) - File overview and Preview
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setHandleWidth(2)
        
        # File overview pane (left)
        file_overview_pane = self._create_file_overview_pane()
        content_splitter.addWidget(file_overview_pane)
        
        # Preview pane (right)
        preview_pane = self._create_preview_pane()
        content_splitter.addWidget(preview_pane)
        
        # Set content splitter sizes (25% file overview, 75% preview)
        content_splitter.setSizes([250, 750])
        
        main_splitter.addWidget(content_splitter)
        
        # Set main splitter sizes (15% settings, 85% content)
        main_splitter.setSizes([120, 680])
        
        self.main_layout.addWidget(main_splitter)
    
    def _create_settings_pane(self) -> QGroupBox:
        """Create the Settings pane."""
        group_box = QGroupBox("Settings")
        group_box.setStyleSheet(f"""
            QGroupBox {{
                font-size: 13px;
                font-weight: bold;
                color: {Colors.TEXT};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        
        layout = QVBoxLayout(group_box)
        layout.setSpacing(10)
        
        # First row: Pickle file path and toggles
        first_row = QHBoxLayout()
        first_row.setSpacing(15)
        
        # Pickle file section
        pickle_label = QLabel("Pickle File:")
        pickle_label.setStyleSheet(f"font-size: 11px; color: {Colors.TEXT}; font-weight: normal;")
        first_row.addWidget(pickle_label)
        
        self.pickle_path_display = QLineEdit()
        self.pickle_path_display.setReadOnly(True)
        self.pickle_path_display.setPlaceholderText("No pickle file loaded")
        self.pickle_path_display.setMinimumWidth(300)
        self.pickle_path_display.setStyleSheet(f"""
            QLineEdit {{
                padding: 4px 8px;
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                background-color: #FFFFFF;
                font-size: 11px;
            }}
        """)
        first_row.addWidget(self.pickle_path_display, 1)
        
        self.browse_button = QPushButton("Browse")
        self.browse_button.setFixedWidth(80)
        self.browse_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_button.setStyleSheet(f"""
            QPushButton {{
                padding: 4px 12px;
                background-color: {Colors.ACCENT};
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {Colors.HOVER};
            }}
        """)
        self.browse_button.clicked.connect(self._on_browse_pickle)
        first_row.addWidget(self.browse_button)
        
        first_row.addSpacing(30)
        
        # File Selection toggle (segmented control)
        file_sel_label = QLabel("File Selection:")
        file_sel_label.setStyleSheet(f"font-size: 11px; color: {Colors.TEXT}; font-weight: normal;")
        first_row.addWidget(file_sel_label)
        
        # Create segmented control for Groups/Singles
        self.file_selection_group = QButtonGroup(self)
        
        self.groups_button = QPushButton("Groups")
        self.groups_button.setCheckable(True)
        self.groups_button.setChecked(True)
        self.groups_button.setFixedWidth(70)
        
        self.singles_button = QPushButton("Singles")
        self.singles_button.setCheckable(True)
        self.singles_button.setFixedWidth(70)
        
        self.file_selection_group.addButton(self.groups_button, 0)
        self.file_selection_group.addButton(self.singles_button, 1)
        
        # Style the segmented control
        segment_style = f"""
            QPushButton {{
                padding: 4px 8px;
                background-color: #FFFFFF;
                color: {Colors.TEXT};
                border: 1px solid {Colors.BORDER};
                font-size: 11px;
            }}
            QPushButton:checked {{
                background-color: {Colors.ACTIVE};
                color: white;
                border: 1px solid {Colors.ACTIVE};
            }}
            QPushButton:hover:!checked {{
                background-color: #F0F0F0;
            }}
        """
        self.groups_button.setStyleSheet(segment_style + "QPushButton { border-top-left-radius: 4px; border-bottom-left-radius: 4px; border-right: none; }")
        self.singles_button.setStyleSheet(segment_style + "QPushButton { border-top-right-radius: 4px; border-bottom-right-radius: 4px; }")
        
        first_row.addWidget(self.groups_button)
        first_row.addWidget(self.singles_button)
        
        self.file_selection_group.idClicked.connect(self._on_file_selection_changed)
        
        first_row.addSpacing(20)
        
        # Composite toggle
        composite_label = QLabel("Composite:")
        composite_label.setStyleSheet(f"font-size: 11px; color: {Colors.TEXT}; font-weight: normal;")
        first_row.addWidget(composite_label)
        
        self.composite_toggle = QCheckBox("ON")
        self.composite_toggle.setChecked(True)
        self.composite_toggle.setEnabled(False)  # Grayed out for now
        self.composite_toggle.setStyleSheet(f"""
            QCheckBox {{
                font-size: 11px;
                color: #999999;
                spacing: 5px;
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
            }}
            QCheckBox::indicator:checked:disabled {{
                border: 2px solid #CCCCCC;
                border-radius: 3px;
                background-color: #CCCCCC;
            }}
        """)
        first_row.addWidget(self.composite_toggle)
        
        first_row.addStretch()
        
        layout.addLayout(first_row)
        
        # Second row: Content toggles
        second_row = QHBoxLayout()
        second_row.setSpacing(20)
        
        # Grayed-out toggle style (always checked, disabled)
        disabled_toggle_style = f"""
            QCheckBox {{
                font-size: 11px;
                color: #999999;
                spacing: 5px;
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
            }}
            QCheckBox::indicator:checked:disabled {{
                border: 2px solid #CCCCCC;
                border-radius: 3px;
                background-color: #CCCCCC;
            }}
        """
        
        self.heatmaps_toggle = QCheckBox("Heatmaps")
        self.heatmaps_toggle.setChecked(True)
        self.heatmaps_toggle.setEnabled(False)
        self.heatmaps_toggle.setStyleSheet(disabled_toggle_style)
        second_row.addWidget(self.heatmaps_toggle)
        
        self.intensity_toggle = QCheckBox("Intensity Distributions")
        self.intensity_toggle.setChecked(True)
        self.intensity_toggle.setEnabled(False)
        self.intensity_toggle.setStyleSheet(disabled_toggle_style)
        second_row.addWidget(self.intensity_toggle)
        
        self.fractions_toggle = QCheckBox("Fractions")
        self.fractions_toggle.setChecked(True)
        self.fractions_toggle.setEnabled(False)
        self.fractions_toggle.setStyleSheet(disabled_toggle_style)
        second_row.addWidget(self.fractions_toggle)
        
        second_row.addStretch()
        
        layout.addLayout(second_row)
        
        return group_box
    
    def _create_file_overview_pane(self) -> QGroupBox:
        """Create the File Overview pane."""
        group_box = QGroupBox("File Overview")
        group_box.setStyleSheet(f"""
            QGroupBox {{
                font-size: 13px;
                font-weight: bold;
                color: {Colors.TEXT};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        
        layout = QVBoxLayout(group_box)
        
        # Scroll area for group toggles
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
        """)
        
        # Container for group toggles
        self.groups_container = QWidget()
        self.groups_layout = QVBoxLayout(self.groups_container)
        self.groups_layout.setSpacing(5)
        self.groups_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Placeholder label for when "Singles" is selected or no data
        self.groups_placeholder = QLabel("No groups available")
        self.groups_placeholder.setStyleSheet(f"""
            QLabel {{
                color: #999999;
                font-size: 11px;
                padding: 20px;
            }}
        """)
        self.groups_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.groups_layout.addWidget(self.groups_placeholder)
        
        scroll_area.setWidget(self.groups_container)
        layout.addWidget(scroll_area)
        
        return group_box
    
    def _create_preview_pane(self) -> QGroupBox:
        """Create the Preview pane with sheet navigation."""
        group_box = QGroupBox("Preview")
        group_box.setStyleSheet(f"""
            QGroupBox {{
                font-size: 13px;
                font-weight: bold;
                color: {Colors.TEXT};
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }}
        """)
        
        layout = QVBoxLayout(group_box)
        
        # Scroll area for sheets
        self.sheets_scroll_area = QScrollArea()
        self.sheets_scroll_area.setWidgetResizable(True)
        self.sheets_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.sheets_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.sheets_scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                background-color: #E0E0E0;
            }}
        """)
        
        # Container for all sheets
        self.sheets_container = QWidget()
        self.sheets_container.setStyleSheet("background-color: #E0E0E0;")
        self.sheets_layout = QVBoxLayout(self.sheets_container)
        self.sheets_layout.setSpacing(20)
        self.sheets_layout.setContentsMargins(20, 20, 20, 20)
        self.sheets_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        
        # Placeholder
        self.preview_placeholder = QLabel("No preview available.\n\nLoad a pickle file and select groups to preview.")
        self.preview_placeholder.setStyleSheet(f"""
            QLabel {{
                color: #999999;
                font-size: 12px;
                padding: 40px;
            }}
        """)
        self.preview_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sheets_layout.addWidget(self.preview_placeholder)
        
        self.sheets_scroll_area.setWidget(self.sheets_container)
        layout.addWidget(self.sheets_scroll_area, 1)
        
        return group_box
    
    # ==================== Callbacks ====================
    
    def set_pickle_data_callback(self, callback: Callable):
        """Set callback to get pickle DataFrame."""
        self._get_pickle_data_callback = callback
    
    def set_pickle_path_callback(self, callback: Callable):
        """Set callback to get pickle file path."""
        self._get_pickle_path_callback = callback
    
    def set_load_pickle_callback(self, callback: Callable):
        """Set callback to load a pickle file (updates all workspaces)."""
        self._load_pickle_file_callback = callback
    
    # ==================== Event Handlers ====================
    
    def _on_browse_pickle(self):
        """Handle Browse button click to select a pickle file."""
        current_path = self._get_pickle_path_callback() if self._get_pickle_path_callback else ""
        default_dir = os.path.dirname(current_path) if current_path else os.getcwd()
        
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Select Pickle File",
            default_dir,
            "Pickle Files (*.pkl);;All Files (*)"
        )
        
        if filepath:
            if self._load_pickle_file_callback:
                try:
                    self._load_pickle_file_callback(filepath)
                    self.pickle_file_changed.emit(filepath)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to load pickle file: {e}")
    
    def _on_file_selection_changed(self, button_id: int):
        """Handle file selection toggle change (Groups/Singles)."""
        if button_id == 0:  # Groups
            self._update_file_overview()
            self._update_preview()
        else:  # Singles
            self._show_singles_placeholder()
    
    def _on_group_toggle_changed(self):
        """Handle group toggle state change."""
        self._update_preview()
    
    def _show_singles_placeholder(self):
        """Show placeholder when Singles mode is selected."""
        # Clear groups
        self._clear_groups_layout()
        
        self.groups_placeholder.setText("Option not yet generated")
        self.groups_placeholder.show()
        
        # Clear preview
        self._clear_preview()
        self.preview_placeholder.setText("Singles mode is not yet implemented.")
        self.preview_placeholder.show()
    
    def _clear_groups_layout(self):
        """Clear all group toggles from the layout."""
        # Remove all widgets except placeholder
        for toggle in list(self._group_toggles.values()):
            self.groups_layout.removeWidget(toggle)
            toggle.deleteLater()
        self._group_toggles.clear()
    
    def _clear_preview(self):
        """Clear all sheets from the preview."""
        # Remove all widgets except placeholder
        while self.sheets_layout.count() > 1:
            item = self.sheets_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()
        
        self._sheets_data.clear()
    
    # ==================== Data Update Methods ====================
    
    def refresh_data(self):
        """Refresh data from the pickle file."""
        if self._get_pickle_data_callback:
            self._dataframe = self._get_pickle_data_callback()
        
        if self._get_pickle_path_callback:
            self._current_pickle_path = self._get_pickle_path_callback()
            if self._current_pickle_path:
                self.pickle_path_display.setText(self._current_pickle_path)
            else:
                self.pickle_path_display.clear()
        
        # Update UI based on current selection
        if self.groups_button.isChecked():
            self._update_file_overview()
            self._update_preview()
        else:
            self._show_singles_placeholder()
    
    def _update_file_overview(self):
        """Update the file overview with group toggles."""
        self._clear_groups_layout()
        
        if self._dataframe is None or self._dataframe.empty:
            self.groups_placeholder.setText("No groups available")
            self.groups_placeholder.show()
            return
        
        # Check if Group column exists
        if "Group" not in self._dataframe.columns:
            self.groups_placeholder.setText("No 'Group' column in pickle file")
            self.groups_placeholder.show()
            return
        
        # Get unique groups with their IDs
        groups_df = self._dataframe[["Group", "Group_ID"]].drop_duplicates()
        groups_df = groups_df[groups_df["Group"] != ""]  # Filter empty groups
        groups_df = groups_df.sort_values("Group_ID")
        
        if groups_df.empty:
            self.groups_placeholder.setText("No groups defined in pickle file")
            self.groups_placeholder.show()
            return
        
        self.groups_placeholder.hide()
        
        # Create toggle for each group
        toggle_style = f"""
            QCheckBox {{
                font-size: 11px;
                color: {Colors.TEXT};
                spacing: 8px;
                padding: 5px;
            }}
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
            }}
            QCheckBox::indicator:unchecked {{
                border: 2px solid {Colors.BORDER};
                border-radius: 3px;
                background-color: #FFFFFF;
            }}
            QCheckBox::indicator:checked {{
                border: 2px solid {Colors.ACTIVE};
                border-radius: 3px;
                background-color: {Colors.ACTIVE};
            }}
        """
        
        for _, row in groups_df.iterrows():
            group_name = row["Group"]
            group_id = int(row["Group_ID"])
            
            toggle = QCheckBox(f"{group_name} ({group_id})")
            toggle.setChecked(True)
            toggle.setStyleSheet(toggle_style)
            toggle.toggled.connect(self._on_group_toggle_changed)
            
            self._group_toggles[group_name] = toggle
            self.groups_layout.addWidget(toggle)
        
        # Add stretch at the end
        self.groups_layout.addStretch()
    
    def _update_preview(self):
        """Update the preview pane with sheets for selected groups."""
        self._clear_preview()
        
        if self._dataframe is None or self._dataframe.empty:
            self.preview_placeholder.setText("No data available.\n\nLoad a pickle file to see preview.")
            self.preview_placeholder.show()
            return
        
        # Check required columns
        required_cols = ["Filename", "Directory", "Group", "Group_ID"]
        missing_cols = [col for col in required_cols if col not in self._dataframe.columns]
        if missing_cols:
            self.preview_placeholder.setText(f"Missing columns: {', '.join(missing_cols)}")
            self.preview_placeholder.show()
            return
        
        # Check for threshold data
        if "Threshold" not in self._dataframe.columns:
            self.preview_placeholder.setText("No threshold data found.\n\nProcess files in the Raw Processing tab first.")
            self.preview_placeholder.show()
            return
        
        # Get selected groups
        selected_groups = [name for name, toggle in self._group_toggles.items() if toggle.isChecked()]
        
        if not selected_groups:
            self.preview_placeholder.setText("No groups selected.\n\nSelect at least one group to preview.")
            self.preview_placeholder.show()
            return
        
        self.preview_placeholder.hide()
        
        # Create a sheet for each selected group
        for group_name in selected_groups:
            group_df = self._dataframe[self._dataframe["Group"] == group_name]
            if group_df.empty:
                continue
            
            group_id = int(group_df.iloc[0]["Group_ID"])
            
            # Create sheet widget
            sheet = self._create_sheet(group_name, group_id, group_df)
            self.sheets_layout.addWidget(sheet)
    
    def _create_sheet(self, group_name: str, group_id: int, group_df: pd.DataFrame) -> QWidget:
        """
        Create a sheet widget for a group.
        
        Args:
            group_name: Name of the group.
            group_id: ID of the group.
            group_df: DataFrame containing only files for this group.
            
        Returns:
            QWidget: The sheet widget with all visualizations.
        """
        # A4 landscape proportions (297mm x 210mm) scaled for display
        sheet_width = 800
        sheet_height = int(sheet_width * 210 / 297)  # ~566 pixels
        
        sheet_widget = QFrame()
        sheet_widget.setFixedSize(sheet_width, sheet_height)
        sheet_widget.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
            }}
        """)
        
        # Create matplotlib figure for this sheet
        fig = Figure(figsize=(sheet_width / 100, sheet_height / 100), dpi=100)
        fig.set_facecolor('white')
        
        canvas = FigureCanvas(fig)
        canvas.setParent(sheet_widget)
        canvas.setGeometry(0, 0, sheet_width, sheet_height)
        
        # Render the sheet content
        self._render_sheet_content(fig, group_name, group_id, group_df)
        
        canvas.draw()
        
        return sheet_widget
    
    def _render_sheet_content(self, fig: Figure, group_name: str, group_id: int, 
                              group_df: pd.DataFrame):
        """
        Render the content of a sheet.
        
        Args:
            fig: Matplotlib figure to render on.
            group_name: Name of the group.
            group_id: ID of the group.
            group_df: DataFrame containing files for this group.
        """
        fig.clear()
        
        num_files = len(group_df)
        if num_files == 0:
            ax = fig.add_subplot(111)
            ax.text(0.5, 0.5, "No files in this group", ha='center', va='center',
                    fontsize=12, color='gray')
            ax.axis('off')
            return
        
        # Get threshold value
        threshold = group_df.iloc[0]["Threshold"]
        
        # Calculate grid layout for heatmaps
        # Aim for roughly square grid, slightly wider for landscape
        n_cols = int(np.ceil(np.sqrt(num_files * 1.2)))
        n_rows = int(np.ceil(num_files / n_cols))
        
        # Define layout: left 55% for heatmaps, right 45% for charts
        # Create GridSpec
        from matplotlib.gridspec import GridSpec
        
        gs = GridSpec(2, 2, figure=fig, width_ratios=[55, 45], height_ratios=[1, 1],
                      left=0.05, right=0.95, top=0.88, bottom=0.08, wspace=0.15, hspace=0.25)
        
        # Add title with group name and ID
        fig.suptitle(f"{group_name} (ID: {group_id})", fontsize=11, fontweight='bold',
                     x=0.05, ha='left')
        
        # Left side: Heatmaps (spanning both rows)
        heatmap_gs = gs[:, 0].subgridspec(n_rows, n_cols, wspace=0.1, hspace=0.2)
        
        # Right side: Intensity distribution (top) and Fractions (bottom)
        intensity_ax = fig.add_subplot(gs[0, 1])
        fractions_ax = fig.add_subplot(gs[1, 1])
        
        # Get file colors
        colors = [self._file_colors[i % len(self._file_colors)] for i in range(num_files)]
        
        # Collect data for composite plots
        file_labels = []
        fraction_values = []
        
        # Render heatmaps and collect data
        for idx, (_, row) in enumerate(group_df.iterrows()):
            if idx >= n_rows * n_cols:
                break
            
            row_idx = idx // n_cols
            col_idx = idx % n_cols
            
            ax = fig.add_subplot(heatmap_gs[row_idx, col_idx])
            
            filename = row["Filename"]
            directory = row["Directory"]
            filepath = os.path.join(directory, filename)
            
            # Get display name (remove group prefix from filename)
            display_name = self._get_display_filename(filename, group_name)
            file_labels.append(display_name)
            
            # Get fraction value
            fraction = row.get("Fraction", np.nan)
            fraction_values.append(fraction)
            
            # Load and display heatmap
            image = self._load_image_silent(filepath)
            if image is not None:
                # Apply threshold mask
                mask = image < threshold
                masked_image = np.ma.masked_where(mask, image)
                
                ax.imshow(masked_image, cmap='viridis', aspect='equal')
                ax.imshow(mask, cmap='Greys', aspect='equal', alpha=mask.astype(float))
                
                # Also plot intensity distribution
                pixels_above = image[image >= threshold]
                if len(pixels_above) > 0:
                    intensity_ax.hist(pixels_above, bins=100, alpha=0.6, 
                                     color=colors[idx], label=display_name,
                                     histtype='step', linewidth=1.5)
            else:
                ax.text(0.5, 0.5, "Failed to load", ha='center', va='center',
                        fontsize=6, color='red', transform=ax.transAxes)
            
            ax.set_title(display_name, fontsize=6, pad=2)
            ax.axis('off')
        
        # Configure intensity distribution plot
        intensity_ax.set_title("Intensity Distributions", fontsize=9, fontweight='bold')
        intensity_ax.set_xlabel("Pixel Value", fontsize=8)
        intensity_ax.set_ylabel("Frequency", fontsize=8)
        intensity_ax.tick_params(labelsize=7)
        if num_files <= 8:
            intensity_ax.legend(fontsize=5, loc='upper right')
        
        # Draw threshold line
        intensity_ax.axvline(x=threshold, color='red', linestyle='--', linewidth=1,
                            label=f'Threshold: {threshold:.1f}')
        
        # Configure fractions bar chart
        x_pos = np.arange(len(file_labels))
        bars = fractions_ax.bar(x_pos, fraction_values, color=colors[:len(file_labels)],
                               edgecolor='black', linewidth=0.5)
        
        fractions_ax.set_title("Fractions Above Threshold", fontsize=9, fontweight='bold')
        fractions_ax.set_xlabel("File", fontsize=8)
        fractions_ax.set_ylabel("Fraction", fontsize=8)
        fractions_ax.set_xticks(x_pos)
        fractions_ax.set_xticklabels(file_labels, rotation=45, ha='right', fontsize=6)
        fractions_ax.tick_params(labelsize=7)
        fractions_ax.set_ylim(0, 1)
        
        # Add value labels on bars
        for bar, val in zip(bars, fraction_values):
            if not np.isnan(val):
                fractions_ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                                 f'{val:.2f}', ha='center', va='bottom', fontsize=5)
    
    def _get_display_filename(self, filename: str, group_name: str) -> str:
        """
        Get display filename by removing group name prefix.
        
        Args:
            filename: The full filename.
            group_name: The group name to remove.
            
        Returns:
            The filename without the group name prefix.
        """
        # Try to remove group name from the beginning
        if filename.startswith(group_name):
            result = filename[len(group_name):]
            # Remove leading separators
            result = result.lstrip('_- ')
            return result if result else filename
        return filename
    
    def _load_image_silent(self, filepath: str) -> np.ndarray | None:
        """
        Load an image from file without showing dialogs.
        
        Args:
            filepath: Full path to the image file.
            
        Returns:
            Image as numpy array, or None if loading fails.
        """
        if not os.path.exists(filepath):
            return None
        
        ext = os.path.splitext(filepath)[1].lower()
        
        try:
            if ext in ['.tif', '.tiff']:
                import tifffile
                image = tifffile.imread(filepath)
            elif ext == '.nd2':
                from nd2reader import ND2Reader
                with ND2Reader(filepath) as nd2:
                    image = np.array(nd2[0])
            else:
                from PIL import Image
                image = np.array(Image.open(filepath))
            
            # Handle multi-channel images
            if image.ndim > 2:
                if image.ndim == 3:
                    if image.shape[2] in [3, 4]:
                        if image.shape[2] == 3:
                            image = np.mean(image, axis=2)
                        else:
                            image = np.mean(image[:, :, :3], axis=2)
                    else:
                        image = image[:, :, 0]
                elif image.ndim == 4:
                    image = image[0, 0, :, :] if image.shape[0] > 1 else image[0, :, :, 0]
            
            return image.astype(np.float64)
            
        except Exception:
            return None
    
    # ==================== Lifecycle Methods ====================
    
    def on_activated(self):
        """Called when Output workspace becomes active."""
        self.refresh_data()
