"""
Groups Tab - For organizing selected files into groups based on naming patterns.
"""

import os
import re
from collections import defaultdict
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QFrame, QComboBox,
    QSpinBox, QPushButton, QCheckBox, QStackedWidget,
    QSplitter, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal

from .base_tab import BaseTab
from ....utils.constants import Colors


class GroupsTab(BaseTab):
    """
    Tab for organizing files into groups based on naming patterns.
    
    Features:
    - Display selected files from Import tab
    - Toggle grouping on/off
    - Group by underscore segments or character positions
    - Preview grouped results
    """
    
    # Signal emitted when grouping configuration changes
    grouping_changed = pyqtSignal(dict)
    
    # Selector types
    SELECTOR_UNDERSCORE = "by underscore"
    SELECTOR_LENGTH = "by length"
    
    @property
    def tab_name(self) -> str:
        return "Groups"
    
    def _init_ui(self):
        """Initialize the Groups tab UI."""
        # Create main horizontal splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("""
            QSplitter::handle {
                background-color: #BDC3C7;
            }
        """)
        
        # Left panel - Selected files list
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Grouping controls
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set initial splitter sizes (40% left, 60% right)
        splitter.setSizes([400, 600])
        
        self.main_layout.addWidget(splitter)
        
        # Initialize state
        self._selected_files: list[str] = []
        self._update_controls_state()
    
    def _create_left_panel(self) -> QFrame:
        """Create the left panel with selected files list."""
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
            }}
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Header
        header = QLabel("📄 Selected Files")
        header.setStyleSheet(f"""
            QLabel {{
                font-size: 13px;
                font-weight: bold;
                color: {Colors.TEXT};
                border: none;
            }}
        """)
        layout.addWidget(header)
        
        # File list
        self.files_list = QListWidget()
        self.files_list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                background-color: #FAFAFA;
                font-size: 11px;
                padding: 5px;
            }}
            QListWidget::item {{
                padding: 5px;
                border-bottom: 1px solid #F0F0F0;
            }}
        """)
        layout.addWidget(self.files_list, 1)
        
        # File count label
        self.file_count_label = QLabel("Total: 0 files")
        self.file_count_label.setStyleSheet(f"""
            QLabel {{
                font-size: 11px;
                color: #7F8C8D;
                border: none;
            }}
        """)
        layout.addWidget(self.file_count_label)
        
        return panel
    
    def _create_right_panel(self) -> QFrame:
        """Create the right panel with grouping controls."""
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: #FFFFFF;
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
            }}
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Toggle checkbox
        self.group_toggle = QCheckBox("Arrange files in groups?")
        self.group_toggle.setStyleSheet(f"""
            QCheckBox {{
                font-size: 13px;
                font-weight: bold;
                color: {Colors.TEXT};
                spacing: 8px;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
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
        self.group_toggle.toggled.connect(self._on_toggle_changed)
        layout.addWidget(self.group_toggle)
        
        # Grouping controls container
        self.controls_container = QWidget()
        controls_layout = QVBoxLayout(self.controls_container)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(15)
        
        # Selector dropdown
        selector_label = QLabel("Define selector:")
        selector_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                font-weight: bold;
                color: {Colors.TEXT};
            }}
        """)
        controls_layout.addWidget(selector_label)
        
        self.selector_combo = QComboBox()
        self.selector_combo.addItems([self.SELECTOR_UNDERSCORE, self.SELECTOR_LENGTH])
        self.selector_combo.setFixedWidth(200)
        self.selector_combo.setStyleSheet(f"""
            QComboBox {{
                padding: 8px 12px;
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                background-color: #FFFFFF;
                font-size: 12px;
                color: {Colors.TEXT};
            }}
            QComboBox:hover {{
                border-color: {Colors.ACCENT};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 30px;
            }}
            QComboBox::down-arrow {{
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {Colors.TEXT};
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: #FFFFFF;
                border: 1px solid {Colors.BORDER};
                selection-background-color: {Colors.ACCENT};
                selection-color: white;
            }}
        """)
        self.selector_combo.currentIndexChanged.connect(self._on_selector_changed)
        controls_layout.addWidget(self.selector_combo)
        
        # Selection criteria section
        criteria_label = QLabel("Selection criteria:")
        criteria_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                font-weight: bold;
                color: {Colors.TEXT};
            }}
        """)
        controls_layout.addWidget(criteria_label)
        
        # Stacked widget for different criteria views
        self.criteria_stack = QStackedWidget()
        self.criteria_stack.setStyleSheet(f"""
            QStackedWidget {{
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                background-color: #FAFAFA;
            }}
        """)
        
        # Underscore criteria
        underscore_widget = self._create_underscore_criteria()
        self.criteria_stack.addWidget(underscore_widget)
        
        # Length criteria
        length_widget = self._create_length_criteria()
        self.criteria_stack.addWidget(length_widget)
        
        controls_layout.addWidget(self.criteria_stack)
        
        # Preview button
        self.preview_button = QPushButton("Preview")
        self.preview_button.setFixedWidth(100)
        self.preview_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.preview_button.setStyleSheet(f"""
            QPushButton {{
                padding: 8px 16px;
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
            QPushButton:disabled {{
                background-color: {Colors.BORDER};
                color: #7F8C8D;
            }}
        """)
        self.preview_button.clicked.connect(self._on_preview_clicked)
        controls_layout.addWidget(self.preview_button)
        
        # Preview results section
        preview_label = QLabel("Preview (first group):")
        preview_label.setStyleSheet(f"""
            QLabel {{
                font-size: 12px;
                font-weight: bold;
                color: {Colors.TEXT};
            }}
        """)
        controls_layout.addWidget(preview_label)
        
        # Preview list
        self.preview_list = QListWidget()
        self.preview_list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                background-color: #FAFAFA;
                font-size: 11px;
                padding: 5px;
            }}
            QListWidget::item {{
                padding: 5px;
                border-bottom: 1px solid #F0F0F0;
            }}
        """)
        self.preview_list.setMinimumHeight(150)
        controls_layout.addWidget(self.preview_list, 1)
        
        layout.addWidget(self.controls_container)
        layout.addStretch()
        
        return panel
    
    def _create_underscore_criteria(self) -> QWidget:
        """Create the underscore-based criteria widget."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)
        
        # Label parts
        label1 = QLabel("Group by content between underscore number")
        label1.setStyleSheet("font-size: 11px;")
        layout.addWidget(label1)
        
        # Start spinbox
        self.underscore_start = QSpinBox()
        self.underscore_start.setMinimum(0)
        self.underscore_start.setMaximum(99)
        self.underscore_start.setValue(0)
        self.underscore_start.setFixedWidth(60)
        self.underscore_start.setStyleSheet(f"""
            QSpinBox {{
                padding: 5px;
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                background-color: #FFFFFF;
            }}
        """)
        layout.addWidget(self.underscore_start)
        
        label2 = QLabel("and")
        label2.setStyleSheet("font-size: 11px;")
        layout.addWidget(label2)
        
        # End spinbox
        self.underscore_end = QSpinBox()
        self.underscore_end.setMinimum(0)
        self.underscore_end.setMaximum(99)
        self.underscore_end.setValue(1)
        self.underscore_end.setFixedWidth(60)
        self.underscore_end.setStyleSheet(f"""
            QSpinBox {{
                padding: 5px;
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                background-color: #FFFFFF;
            }}
        """)
        layout.addWidget(self.underscore_end)
        
        layout.addStretch()
        
        return widget
    
    def _create_length_criteria(self) -> QWidget:
        """Create the length-based criteria widget."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(5)
        
        # Label parts
        label1 = QLabel("Group by content from character number")
        label1.setStyleSheet("font-size: 11px;")
        layout.addWidget(label1)
        
        # Start spinbox (1-indexed for user)
        self.length_start = QSpinBox()
        self.length_start.setMinimum(1)
        self.length_start.setMaximum(999)
        self.length_start.setValue(1)
        self.length_start.setFixedWidth(60)
        self.length_start.setStyleSheet(f"""
            QSpinBox {{
                padding: 5px;
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                background-color: #FFFFFF;
            }}
        """)
        layout.addWidget(self.length_start)
        
        label2 = QLabel("to number")
        label2.setStyleSheet("font-size: 11px;")
        layout.addWidget(label2)
        
        # End spinbox
        self.length_end = QSpinBox()
        self.length_end.setMinimum(1)
        self.length_end.setMaximum(999)
        self.length_end.setValue(6)
        self.length_end.setFixedWidth(60)
        self.length_end.setStyleSheet(f"""
            QSpinBox {{
                padding: 5px;
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                background-color: #FFFFFF;
            }}
        """)
        layout.addWidget(self.length_end)
        
        layout.addStretch()
        
        return widget
    
    def _update_controls_state(self):
        """Update the enabled state of controls based on toggle."""
        enabled = self.group_toggle.isChecked()
        self.controls_container.setEnabled(enabled)
        
        # Update visual style for disabled state
        opacity = "1.0" if enabled else "0.5"
        self.controls_container.setStyleSheet(f"opacity: {opacity};")
    
    def _on_toggle_changed(self, checked: bool):
        """Handle grouping toggle change."""
        self._update_controls_state()
        if not checked:
            self.preview_list.clear()
        self._emit_grouping_changed()
    
    def _on_selector_changed(self, index: int):
        """Handle selector dropdown change."""
        self.criteria_stack.setCurrentIndex(index)
        self.preview_list.clear()
    
    def _on_preview_clicked(self):
        """Handle preview button click."""
        self._generate_preview()
    
    def _extract_group_key(self, filename: str) -> str | None:
        """
        Extract the group key from a filename based on current criteria.
        
        Args:
            filename: The filename (without path) to extract key from.
            
        Returns:
            The group key, or None if extraction fails.
        """
        # Remove file extension for grouping
        name_without_ext = os.path.splitext(filename)[0]
        
        selector = self.selector_combo.currentText()
        
        if selector == self.SELECTOR_UNDERSCORE:
            # Split by underscore and extract segments
            parts = name_without_ext.split('_')
            start = self.underscore_start.value()
            end = self.underscore_end.value()
            
            # Validate indices
            if start >= len(parts) or end > len(parts) or start >= end:
                return None
            
            # Extract and join the selected parts
            selected_parts = parts[start:end]
            return '_'.join(selected_parts)
        
        elif selector == self.SELECTOR_LENGTH:
            # Extract by character positions (1-indexed in UI)
            start = self.length_start.value() - 1  # Convert to 0-indexed
            end = self.length_end.value()  # End is inclusive in UI, so no -1
            
            # Validate indices
            if start < 0 or end > len(name_without_ext) or start >= end:
                return None
            
            return name_without_ext[start:end]
        
        return None
    
    def _generate_preview(self):
        """Generate and display the preview of grouping."""
        self.preview_list.clear()
        
        if not self._selected_files:
            self.preview_list.addItem("No files selected")
            return
        
        # Group files
        groups = defaultdict(list)
        ungrouped = []
        
        for filepath in self._selected_files:
            filename = os.path.basename(filepath)
            key = self._extract_group_key(filename)
            
            if key:
                groups[key].append(filename)
            else:
                ungrouped.append(filename)
        
        if not groups:
            self.preview_list.addItem("No valid groups found")
            if ungrouped:
                self.preview_list.addItem(f"({len(ungrouped)} files couldn't be grouped)")
            return
        
        # Get first group (sorted alphabetically)
        first_key = sorted(groups.keys())[0]
        first_group_files = sorted(groups[first_key])
        
        # Display group info
        header_item = QListWidgetItem(f"📁 Group: \"{first_key}\"")
        header_item.setBackground(Qt.GlobalColor.lightGray)
        self.preview_list.addItem(header_item)
        
        # Add files in this group
        for filename in first_group_files:
            self.preview_list.addItem(f"   • {filename}")
        
        # Show summary
        summary = f"\n({len(groups)} total groups found)"
        self.preview_list.addItem(summary)
    
    def _emit_grouping_changed(self):
        """Emit signal with current grouping configuration."""
        config = self.get_grouping_config()
        self.grouping_changed.emit(config)
    
    def set_selected_files(self, files: list[str]):
        """
        Update the list of selected files.
        
        Args:
            files: List of file paths.
        """
        self._selected_files = files.copy()
        
        # Update the files list display
        self.files_list.clear()
        for filepath in files:
            filename = os.path.basename(filepath)
            self.files_list.addItem(filename)
        
        # Update count label
        count = len(files)
        self.file_count_label.setText(f"Total: {count} file{'s' if count != 1 else ''}")
        
        # Clear preview when files change
        self.preview_list.clear()
    
    def get_grouping_config(self) -> dict:
        """
        Get the current grouping configuration.
        
        Returns:
            dict: Configuration including enabled state and criteria.
        """
        selector = self.selector_combo.currentText()
        
        config = {
            "enabled": self.group_toggle.isChecked(),
            "selector": selector,
        }
        
        if selector == self.SELECTOR_UNDERSCORE:
            config["start"] = self.underscore_start.value()
            config["end"] = self.underscore_end.value()
        else:
            config["start"] = self.length_start.value()
            config["end"] = self.length_end.value()
        
        return config
    
    def get_grouped_files(self) -> dict[str, list[str]]:
        """
        Get files organized into groups based on current settings.
        
        Returns:
            dict: Mapping of group keys to lists of file paths.
                  If grouping is disabled, returns single group with all files.
        """
        if not self.group_toggle.isChecked():
            return {"all": self._selected_files.copy()}
        
        groups = defaultdict(list)
        
        for filepath in self._selected_files:
            filename = os.path.basename(filepath)
            key = self._extract_group_key(filename)
            
            if key:
                groups[key].append(filepath)
            else:
                groups["_ungrouped"].append(filepath)
        
        return dict(groups)
    
    def on_tab_selected(self):
        """Called when this tab becomes active."""
        # Preview could be refreshed here if needed
        pass
    
    def get_data(self) -> dict:
        """Get the current tab data."""
        return {
            "grouping_config": self.get_grouping_config(),
            "grouped_files": self.get_grouped_files(),
        }

