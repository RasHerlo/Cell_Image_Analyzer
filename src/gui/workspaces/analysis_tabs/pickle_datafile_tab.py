"""
Pickle DataFile Tab - For creating, loading, and managing pickle data files.
"""

import os
import pickle
from pathlib import Path
from typing import Callable

import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QCheckBox, QTableWidget,
    QTableWidgetItem, QFileDialog, QMessageBox, QHeaderView,
    QFrame, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from .base_tab import BaseTab
from ....utils.constants import Colors


class PickleDataFileTab(BaseTab):
    """
    Tab for managing pickle data files.
    
    Features:
    - Create new pickle files from selected images
    - Load existing pickle files
    - Display DataFrame contents in scrollable table
    - Sort by groups option
    - Save changes
    """
    
    # Signal emitted when pickle file is loaded/created
    pickle_loaded = pyqtSignal(str)  # Emits file path
    
    # Column names for new pickle files (in order)
    COL_FILENAME = "Filename"
    COL_DIRECTORY = "Directory"
    COL_GROUP = "Group"
    COL_GROUP_ID = "Group_ID"
    
    @property
    def tab_name(self) -> str:
        return "Pickle DataFile"
    
    def _init_ui(self):
        """Initialize the Pickle DataFile tab UI."""
        # Current pickle file path
        self._current_pickle_path: str | None = None
        self._dataframe: pd.DataFrame | None = None
        self._has_unsaved_changes: bool = False
        
        # Callback to get data from Input workspace
        self._get_input_data_callback: Callable | None = None
        
        # Directory section
        self._create_directory_section()
        
        # Buttons section
        self._create_buttons_section()
        
        # Display section
        self._create_display_section()
    
    def _create_directory_section(self):
        """Create the current directory display."""
        # Section label
        dir_label = QLabel("Current Directory:")
        dir_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                font-weight: bold;
                color: {Colors.TEXT};
            }}
        """)
        self.main_layout.addWidget(dir_label)
        
        # Directory path display
        self.directory_display = QLineEdit()
        self.directory_display.setReadOnly(True)
        self.directory_display.setPlaceholderText("No pickle file selected")
        self.directory_display.setStyleSheet(f"""
            QLineEdit {{
                padding: 8px 12px;
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                background-color: #FFFFFF;
                font-size: 12px;
                color: {Colors.TEXT};
            }}
        """)
        self.main_layout.addWidget(self.directory_display)
    
    def _create_buttons_section(self):
        """Create the action buttons and options."""
        # Buttons row
        buttons_row = QHBoxLayout()
        buttons_row.setSpacing(10)
        
        # Start New button
        self.start_new_button = QPushButton("Start New")
        self.start_new_button.setFixedWidth(120)
        self.start_new_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_new_button.setStyleSheet(f"""
            QPushButton {{
                padding: 10px 20px;
                background-color: {Colors.ACTIVE};
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #16A085;
            }}
            QPushButton:pressed {{
                background-color: #0E6655;
            }}
        """)
        self.start_new_button.clicked.connect(self._on_start_new)
        buttons_row.addWidget(self.start_new_button)
        
        # Load Existing button
        self.load_existing_button = QPushButton("Load Existing")
        self.load_existing_button.setFixedWidth(120)
        self.load_existing_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.load_existing_button.setStyleSheet(f"""
            QPushButton {{
                padding: 10px 20px;
                background-color: {Colors.ACCENT};
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Colors.HOVER};
            }}
            QPushButton:pressed {{
                background-color: {Colors.PRIMARY};
            }}
        """)
        self.load_existing_button.clicked.connect(self._on_load_existing)
        buttons_row.addWidget(self.load_existing_button)
        
        # Sort by groups checkbox
        self.sort_by_groups_checkbox = QCheckBox("Sort by groups")
        self.sort_by_groups_checkbox.setStyleSheet(f"""
            QCheckBox {{
                font-size: 12px;
                color: {Colors.TEXT};
                spacing: 8px;
                margin-left: 20px;
            }}
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
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
        """)
        self.sort_by_groups_checkbox.toggled.connect(self._on_sort_toggled)
        buttons_row.addWidget(self.sort_by_groups_checkbox)
        
        buttons_row.addStretch()
        
        # Save button (dormant until changes made)
        self.save_button = QPushButton("Save")
        self.save_button.setFixedWidth(100)
        self.save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_button.setEnabled(False)
        self.save_button.setStyleSheet(f"""
            QPushButton {{
                padding: 10px 20px;
                background-color: {Colors.SECONDARY};
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Colors.HOVER};
            }}
            QPushButton:disabled {{
                background-color: {Colors.BORDER};
                color: #95A5A6;
            }}
        """)
        self.save_button.clicked.connect(self._on_save)
        buttons_row.addWidget(self.save_button)
        
        self.main_layout.addLayout(buttons_row)
    
    def _create_display_section(self):
        """Create the pickle data display table."""
        # Section label
        display_label = QLabel("Pickle Display:")
        display_label.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                font-weight: bold;
                color: {Colors.TEXT};
                margin-top: 10px;
            }}
        """)
        self.main_layout.addWidget(display_label)
        
        # Table widget for DataFrame display
        self.data_table = QTableWidget()
        self.data_table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                background-color: #FFFFFF;
                gridline-color: #E0E0E0;
                font-size: 11px;
            }}
            QTableWidget::item {{
                padding: 5px;
            }}
            QTableWidget::item:selected {{
                background-color: {Colors.ACCENT};
                color: white;
            }}
            QHeaderView::section {{
                background-color: {Colors.SECONDARY};
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
                font-size: 11px;
            }}
            QTableCornerButton::section {{
                background-color: {Colors.SECONDARY};
                border: none;
            }}
        """)
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setMinimumHeight(300)
        
        # Enable scrolling
        self.data_table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.data_table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        
        self.main_layout.addWidget(self.data_table, 1)  # stretch factor 1
    
    def set_input_data_callback(self, callback: Callable):
        """
        Set the callback function to get data from Input workspace.
        
        Args:
            callback: Function that returns dict with 'selected_files' and 'grouped_files'
        """
        self._get_input_data_callback = callback
    
    def _get_default_directory(self) -> str:
        """Get the default directory for file dialogs."""
        # First priority: current pickle file directory
        if self._current_pickle_path:
            return os.path.dirname(self._current_pickle_path)
        
        # Second priority: Input workspace directory
        if self._get_input_data_callback:
            try:
                input_data = self._get_input_data_callback()
                selected_files = input_data.get('selected_files', [])
                if selected_files:
                    return os.path.dirname(selected_files[0])
            except Exception:
                pass
        
        # Fallback: current working directory
        return os.getcwd()
    
    def _get_image_directory_from_input(self) -> str | None:
        """Get the image directory from the Input workspace."""
        if self._get_input_data_callback:
            try:
                input_data = self._get_input_data_callback()
                selected_files = input_data.get('selected_files', [])
                if selected_files:
                    return os.path.dirname(selected_files[0])
            except Exception:
                pass
        return None
    
    def _on_start_new(self):
        """Handle Start New button click."""
        if not self._get_input_data_callback:
            QMessageBox.warning(
                self,
                "No Input Data",
                "Please select files in the Input workspace first."
            )
            return
        
        # Get data from Input workspace
        try:
            input_data = self._get_input_data_callback()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to get input data: {e}")
            return
        
        selected_files = input_data.get('selected_files', [])
        grouped_files = input_data.get('grouped_files', {})
        grouping_enabled = input_data.get('grouping_enabled', False)
        
        if not selected_files:
            QMessageBox.warning(
                self,
                "No Files Selected",
                "Please select files in the Input workspace first."
            )
            return
        
        # Get the base directory from the first selected file
        base_directory = os.path.dirname(selected_files[0])
        
        # Create DataFrame
        data = []
        group_number_map = {}  # Map group names to continuous numbers
        current_group_num = 0
        
        if grouping_enabled and grouped_files:
            # Process files with groups
            for group_name, files in sorted(grouped_files.items()):
                if group_name == "_ungrouped":
                    # Handle ungrouped files
                    for filepath in files:
                        filename = os.path.basename(filepath)
                        data.append({
                            self.COL_FILENAME: filename,
                            self.COL_DIRECTORY: base_directory,
                            self.COL_GROUP: "",
                            self.COL_GROUP_ID: 0
                        })
                else:
                    # Assign group number
                    if group_name not in group_number_map:
                        current_group_num += 1
                        group_number_map[group_name] = current_group_num
                    
                    group_num = group_number_map[group_name]
                    
                    for filepath in files:
                        filename = os.path.basename(filepath)
                        data.append({
                            self.COL_FILENAME: filename,
                            self.COL_DIRECTORY: base_directory,
                            self.COL_GROUP: group_name,
                            self.COL_GROUP_ID: group_num
                        })
        else:
            # No grouping - just filenames with directory
            for filepath in selected_files:
                filename = os.path.basename(filepath)
                data.append({
                    self.COL_FILENAME: filename,
                    self.COL_DIRECTORY: base_directory,
                    self.COL_GROUP: "",
                    self.COL_GROUP_ID: 0
                })
        
        # Create DataFrame with explicit column order
        column_order = [self.COL_FILENAME, self.COL_DIRECTORY, self.COL_GROUP, self.COL_GROUP_ID]
        self._dataframe = pd.DataFrame(data, columns=column_order)
        
        # Apply sorting if checkbox is checked
        if self.sort_by_groups_checkbox.isChecked():
            self._apply_group_sorting()
        
        # Ask for save location
        default_dir = self._get_default_directory()
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save New Pickle File",
            os.path.join(default_dir, "analysis_data.pkl"),
            "Pickle Files (*.pkl);;All Files (*)"
        )
        
        if filepath:
            # Ensure .pkl extension
            if not filepath.endswith('.pkl'):
                filepath += '.pkl'
            
            # Save the pickle file
            try:
                self._dataframe.to_pickle(filepath)
                self._current_pickle_path = filepath
                self._has_unsaved_changes = False
                self._update_display()
                self.directory_display.setText(filepath)
                self.save_button.setEnabled(False)
                self.pickle_loaded.emit(filepath)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save pickle file: {e}")
    
    def _on_load_existing(self):
        """Handle Load Existing button click."""
        default_dir = self._get_default_directory()
        
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Load Existing Pickle File",
            default_dir,
            "Pickle Files (*.pkl);;All Files (*)"
        )
        
        if filepath:
            try:
                # Load the pickle file
                df = pd.read_pickle(filepath)
                
                # Validate it has Filename column
                if self.COL_FILENAME not in df.columns:
                    QMessageBox.warning(
                        self,
                        "Invalid File",
                        f"The pickle file must contain a '{self.COL_FILENAME}' column."
                    )
                    return
                
                # Check if Directory column exists
                if self.COL_DIRECTORY not in df.columns:
                    # Prompt user to select directory
                    directory = self._prompt_for_directory(filepath)
                    if directory is None:
                        # User cancelled
                        return
                    
                    # Add Directory column right after Filename
                    df.insert(1, self.COL_DIRECTORY, directory)
                    
                    # Save the updated pickle file automatically (required field)
                    try:
                        df.to_pickle(filepath)
                        QMessageBox.information(
                            self,
                            "Directory Added",
                            f"The Directory column has been added and saved to the pickle file."
                        )
                    except Exception as e:
                        QMessageBox.critical(
                            self,
                            "Error",
                            f"Failed to save updated pickle file: {e}"
                        )
                        return
                
                self._dataframe = df
                self._current_pickle_path = filepath
                self._has_unsaved_changes = False
                self._update_display()
                self.directory_display.setText(filepath)
                self.save_button.setEnabled(False)
                self.pickle_loaded.emit(filepath)
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load pickle file: {e}")
    
    def _prompt_for_directory(self, pickle_filepath: str) -> str | None:
        """
        Prompt the user to select a directory for image files.
        
        Args:
            pickle_filepath: Path to the pickle file being loaded.
            
        Returns:
            Selected directory path, or None if cancelled.
        """
        # Show info message first
        QMessageBox.information(
            self,
            "Directory Required",
            "The loaded pickle file does not contain a Directory column.\n\n"
            "Please select the directory where the image files are located."
        )
        
        # Determine default directory for the dialog
        # First try Input workspace directory, then pickle file directory
        default_dir = self._get_image_directory_from_input()
        if not default_dir:
            default_dir = os.path.dirname(pickle_filepath)
        
        # Open directory selection dialog
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Image Files Directory",
            default_dir,
            QFileDialog.Option.ShowDirsOnly
        )
        
        if directory:
            return directory
        return None
    
    def _on_sort_toggled(self, checked: bool):
        """Handle sort by groups checkbox toggle."""
        if self._dataframe is not None and not self._dataframe.empty:
            if checked:
                self._apply_group_sorting()
            else:
                # Sort by filename if unchecked
                self._dataframe = self._dataframe.sort_values(
                    by=self.COL_FILENAME,
                    ignore_index=True
                )
            
            self._has_unsaved_changes = True
            self.save_button.setEnabled(True)
            self._update_display()
    
    def _apply_group_sorting(self):
        """Sort the DataFrame by groups."""
        if self._dataframe is None:
            return
        
        sort_columns = []
        if self.COL_GROUP_ID in self._dataframe.columns:
            sort_columns.append(self.COL_GROUP_ID)
        if self.COL_GROUP in self._dataframe.columns:
            sort_columns.append(self.COL_GROUP)
        sort_columns.append(self.COL_FILENAME)
        
        # Only sort by columns that exist
        existing_cols = [c for c in sort_columns if c in self._dataframe.columns]
        if existing_cols:
            self._dataframe = self._dataframe.sort_values(
                by=existing_cols,
                ignore_index=True
            )
    
    def _on_save(self):
        """Handle Save button click."""
        if self._dataframe is None or self._current_pickle_path is None:
            return
        
        try:
            self._dataframe.to_pickle(self._current_pickle_path)
            self._has_unsaved_changes = False
            self.save_button.setEnabled(False)
            QMessageBox.information(self, "Saved", "Pickle file saved successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save pickle file: {e}")
    
    def _update_display(self):
        """Update the table display with current DataFrame."""
        if self._dataframe is None or self._dataframe.empty:
            self.data_table.clear()
            self.data_table.setRowCount(0)
            self.data_table.setColumnCount(0)
            return
        
        # Set table dimensions
        rows, cols = self._dataframe.shape
        self.data_table.setRowCount(rows)
        self.data_table.setColumnCount(cols)
        
        # Set headers
        self.data_table.setHorizontalHeaderLabels(list(self._dataframe.columns))
        
        # Populate table
        for row_idx in range(rows):
            for col_idx in range(cols):
                value = self._dataframe.iloc[row_idx, col_idx]
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)  # Read-only
                self.data_table.setItem(row_idx, col_idx, item)
        
        # Resize columns to content
        self.data_table.resizeColumnsToContents()
        
        # Set minimum column width
        for col_idx in range(cols):
            if self.data_table.columnWidth(col_idx) < 100:
                self.data_table.setColumnWidth(col_idx, 100)
    
    def get_dataframe(self) -> pd.DataFrame | None:
        """
        Get the current DataFrame.
        
        Returns:
            The current DataFrame or None if not loaded.
        """
        return self._dataframe
    
    def get_pickle_path(self) -> str | None:
        """
        Get the current pickle file path.
        
        Returns:
            The file path or None if not set.
        """
        return self._current_pickle_path
    
    def update_dataframe(self, df: pd.DataFrame, filepath: str):
        """
        Update the DataFrame from an external source.
        
        This is called when another tab has modified and saved the DataFrame.
        
        Args:
            df: The updated DataFrame.
            filepath: The path where the DataFrame was saved.
        """
        self._dataframe = df
        self._current_pickle_path = filepath
        self._has_unsaved_changes = False
        self._update_display()
        self.directory_display.setText(filepath)
        self.save_button.setEnabled(False)
    
    def load_pickle_from_path(self, filepath: str):
        """
        Load a pickle file from a given path.
        
        This is called when a pickle file is selected from another workspace.
        
        Args:
            filepath: Path to the pickle file to load.
        """
        try:
            # Load the pickle file
            df = pd.read_pickle(filepath)
            
            # Validate it has Filename column
            if self.COL_FILENAME not in df.columns:
                QMessageBox.warning(
                    self,
                    "Invalid File",
                    f"The pickle file must contain a '{self.COL_FILENAME}' column."
                )
                return
            
            # Check if Directory column exists
            if self.COL_DIRECTORY not in df.columns:
                # Prompt user to select directory
                directory = self._prompt_for_directory(filepath)
                if directory is None:
                    # User cancelled
                    return
                
                # Add Directory column right after Filename
                df.insert(1, self.COL_DIRECTORY, directory)
                
                # Save the updated pickle file
                try:
                    df.to_pickle(filepath)
                    QMessageBox.information(
                        self,
                        "Directory Added",
                        f"The Directory column has been added and saved to the pickle file."
                    )
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Error",
                        f"Failed to save updated pickle file: {e}"
                    )
                    return
            
            self._dataframe = df
            self._current_pickle_path = filepath
            self._has_unsaved_changes = False
            self._update_display()
            self.directory_display.setText(filepath)
            self.save_button.setEnabled(False)
            self.pickle_loaded.emit(filepath)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load pickle file: {e}")
    
    def get_data(self) -> dict:
        """Get the current tab data."""
        return {
            "pickle_path": self._current_pickle_path,
            "has_unsaved_changes": self._has_unsaved_changes,
            "row_count": len(self._dataframe) if self._dataframe is not None else 0,
        }
