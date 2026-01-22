"""
Raw Processing Tab - For analyzing raw image data and generating previews.
"""

import os
import warnings
from typing import Callable

import numpy as np
import pandas as pd
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton, QCheckBox,
    QGroupBox, QSplitter, QFrame, QComboBox, QDoubleSpinBox,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal

# Matplotlib imports for embedding in PyQt6
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from .base_tab import BaseTab
from ....utils.constants import Colors


class RawProcessingTab(BaseTab):
    """
    Tab for raw image processing and analysis.
    
    Features:
    - Fluorescence intensity analysis options
    - File selection for preview
    - Image heatmap and histogram visualization
    - Y-axis scaling controls (linear/log, min/max)
    """
    
    @property
    def tab_name(self) -> str:
        return "Raw Processing"
    
    def _init_ui(self):
        """Initialize the Raw Processing tab UI."""
        # Callback to get pickle data
        self._get_pickle_data_callback: Callable | None = None
        self._current_image: np.ndarray | None = None
        
        # Create main layout with splitters
        main_splitter = QSplitter(Qt.Orientation.Vertical)
        main_splitter.setHandleWidth(2)
        
        # Top pane - Fluorescence Intensities
        fluorescence_pane = self._create_fluorescence_pane()
        main_splitter.addWidget(fluorescence_pane)
        
        # Bottom section - File list and Preview
        bottom_splitter = QSplitter(Qt.Orientation.Horizontal)
        bottom_splitter.setHandleWidth(2)
        
        # File for preview pane (left)
        file_pane = self._create_file_pane()
        bottom_splitter.addWidget(file_pane)
        
        # Preview figures pane (right)
        preview_pane = self._create_preview_pane()
        bottom_splitter.addWidget(preview_pane)
        
        # Set bottom splitter sizes (25% file list, 75% preview)
        bottom_splitter.setSizes([250, 750])
        
        main_splitter.addWidget(bottom_splitter)
        
        # Set main splitter sizes (20% top, 80% bottom)
        main_splitter.setSizes([150, 600])
        
        self.main_layout.addWidget(main_splitter)
    
    def _create_fluorescence_pane(self) -> QGroupBox:
        """Create the Fluorescence Intensities pane."""
        group_box = QGroupBox("Fluorescence Intensities")
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
        
        # Pixel Intensities row
        pixel_row = QHBoxLayout()
        pixel_row.setSpacing(15)
        
        # Toggle checkbox
        self.pixel_intensities_toggle = QCheckBox("Pixel Intensities")
        self.pixel_intensities_toggle.setStyleSheet(f"""
            QCheckBox {{
                font-size: 12px;
                color: {Colors.TEXT};
                spacing: 8px;
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
        pixel_row.addWidget(self.pixel_intensities_toggle)
        
        pixel_row.addStretch()
        
        # Preview button
        self.pixel_preview_button = QPushButton("Preview")
        self.pixel_preview_button.setFixedWidth(100)
        self.pixel_preview_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.pixel_preview_button.setStyleSheet(f"""
            QPushButton {{
                padding: 6px 16px;
                background-color: {Colors.ACCENT};
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Colors.HOVER};
            }}
            QPushButton:pressed {{
                background-color: {Colors.PRIMARY};
            }}
        """)
        self.pixel_preview_button.clicked.connect(self._on_pixel_preview)
        pixel_row.addWidget(self.pixel_preview_button)
        
        layout.addLayout(pixel_row)
        
        # Placeholder for future analysis options
        # (More toggle buttons can be added here)
        
        layout.addStretch()
        
        return group_box
    
    def _create_file_pane(self) -> QGroupBox:
        """Create the File for preview pane."""
        group_box = QGroupBox("File for preview")
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
        
        # File list
        self.file_list = QListWidget()
        self.file_list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                background-color: #FFFFFF;
                font-size: 11px;
                padding: 5px;
            }}
            QListWidget::item {{
                padding: 5px;
                border-bottom: 1px solid #F0F0F0;
            }}
            QListWidget::item:selected {{
                background-color: {Colors.ACCENT};
                color: white;
            }}
            QListWidget::item:hover:!selected {{
                background-color: #F0F0F0;
            }}
        """)
        self.file_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        layout.addWidget(self.file_list)
        
        return group_box
    
    def _create_preview_pane(self) -> QGroupBox:
        """Create the Preview Figures pane."""
        group_box = QGroupBox("Preview Figures")
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
        
        # Y-axis controls for histogram
        controls_row = QHBoxLayout()
        controls_row.setSpacing(15)
        
        # Scale type dropdown
        scale_label = QLabel("Y-axis scale:")
        scale_label.setStyleSheet(f"font-size: 11px; color: {Colors.TEXT};")
        controls_row.addWidget(scale_label)
        
        self.scale_combo = QComboBox()
        self.scale_combo.addItems(["Linear", "Logarithmic"])
        self.scale_combo.setFixedWidth(100)
        self.scale_combo.setStyleSheet(f"""
            QComboBox {{
                padding: 4px 8px;
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                background-color: #FFFFFF;
                font-size: 11px;
            }}
        """)
        self.scale_combo.currentIndexChanged.connect(self._on_scale_changed)
        controls_row.addWidget(self.scale_combo)
        
        controls_row.addSpacing(20)
        
        # Y-axis min
        ymin_label = QLabel("Y min:")
        ymin_label.setStyleSheet(f"font-size: 11px; color: {Colors.TEXT};")
        controls_row.addWidget(ymin_label)
        
        self.ymin_spin = QDoubleSpinBox()
        self.ymin_spin.setRange(0, 1e10)
        self.ymin_spin.setValue(0)
        self.ymin_spin.setDecimals(0)
        self.ymin_spin.setFixedWidth(80)
        self.ymin_spin.setStyleSheet(f"""
            QDoubleSpinBox {{
                padding: 4px;
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                font-size: 11px;
            }}
        """)
        self.ymin_spin.valueChanged.connect(self._on_ylim_changed)
        controls_row.addWidget(self.ymin_spin)
        
        # Y-axis max
        ymax_label = QLabel("Y max:")
        ymax_label.setStyleSheet(f"font-size: 11px; color: {Colors.TEXT};")
        controls_row.addWidget(ymax_label)
        
        self.ymax_spin = QDoubleSpinBox()
        self.ymax_spin.setRange(0, 1e10)
        self.ymax_spin.setValue(0)  # 0 means auto
        self.ymax_spin.setDecimals(0)
        self.ymax_spin.setFixedWidth(80)
        self.ymax_spin.setStyleSheet(f"""
            QDoubleSpinBox {{
                padding: 4px;
                border: 1px solid {Colors.BORDER};
                border-radius: 4px;
                font-size: 11px;
            }}
        """)
        self.ymax_spin.valueChanged.connect(self._on_ylim_changed)
        controls_row.addWidget(self.ymax_spin)
        
        # Auto button
        self.auto_button = QPushButton("Auto")
        self.auto_button.setFixedWidth(60)
        self.auto_button.setStyleSheet(f"""
            QPushButton {{
                padding: 4px 8px;
                background-color: {Colors.SECONDARY};
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: {Colors.HOVER};
            }}
        """)
        self.auto_button.clicked.connect(self._on_auto_ylim)
        controls_row.addWidget(self.auto_button)
        
        controls_row.addStretch()
        layout.addLayout(controls_row)
        
        # Matplotlib figure canvas
        self.figure = Figure(figsize=(10, 5), dpi=100)
        self.figure.set_facecolor('#FAFAFA')
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setStyleSheet("background-color: #FAFAFA;")
        layout.addWidget(self.canvas, 1)
        
        return group_box
    
    def set_pickle_data_callback(self, callback: Callable):
        """
        Set the callback function to get pickle DataFrame.
        
        Args:
            callback: Function that returns the current DataFrame.
        """
        self._get_pickle_data_callback = callback
    
    def refresh_file_list(self):
        """Refresh the file list from the pickle DataFrame."""
        self.file_list.clear()
        
        if not self._get_pickle_data_callback:
            return
        
        try:
            df = self._get_pickle_data_callback()
            if df is None or df.empty:
                return
            
            # Get filenames from DataFrame
            if "Filename" not in df.columns:
                return
            
            filenames = df["Filename"].tolist()
            
            for filename in filenames:
                item = QListWidgetItem(filename)
                self.file_list.addItem(item)
            
            # Select first item by default
            if self.file_list.count() > 0:
                self.file_list.setCurrentRow(0)
                
        except Exception as e:
            print(f"Error refreshing file list: {e}")
    
    def _get_selected_file_info(self) -> tuple[str, str] | None:
        """
        Get the directory and filename for the selected file.
        
        Returns:
            Tuple of (directory, filename) or None if not available.
        """
        # Get selected item
        current_item = self.file_list.currentItem()
        if not current_item:
            return None
        
        filename = current_item.text()
        
        # Get directory from DataFrame
        if not self._get_pickle_data_callback:
            return None
        
        try:
            df = self._get_pickle_data_callback()
            if df is None or df.empty:
                return None
            
            if "Directory" not in df.columns:
                QMessageBox.warning(
                    self,
                    "Missing Directory",
                    "The pickle file does not contain a Directory column."
                )
                return None
            
            # Find the directory for this filename
            row = df[df["Filename"] == filename]
            if row.empty:
                return None
            
            directory = row.iloc[0]["Directory"]
            return (directory, filename)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to get file info: {e}")
            return None
    
    def _load_image(self, filepath: str) -> np.ndarray | None:
        """
        Load an image from file.
        
        Args:
            filepath: Full path to the image file.
            
        Returns:
            Image as numpy array, or None if loading fails.
        """
        if not os.path.exists(filepath):
            QMessageBox.warning(
                self,
                "File Not Found",
                f"The file does not exist:\n{filepath}"
            )
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
                # Try PIL for other formats
                from PIL import Image
                image = np.array(Image.open(filepath))
            
            # Handle multi-channel images
            if image.ndim > 2:
                # Check if it's a multi-channel image
                if image.ndim == 3:
                    if image.shape[2] in [3, 4]:
                        # RGB or RGBA - convert to grayscale
                        if image.shape[2] == 3:
                            image = np.mean(image, axis=2)
                        else:
                            image = np.mean(image[:, :, :3], axis=2)
                        QMessageBox.warning(
                            self,
                            "Multi-channel Image",
                            "RGB image detected. Converted to grayscale (mean of channels)."
                        )
                    else:
                        # Multiple channels - take first
                        image = image[:, :, 0]
                        QMessageBox.warning(
                            self,
                            "Multi-channel Image",
                            f"Multi-channel image detected ({image.shape[2]} channels). "
                            "Showing first channel only."
                        )
                elif image.ndim == 4:
                    # Time series or z-stack with channels
                    image = image[0, 0, :, :] if image.shape[0] > 1 else image[0, :, :, 0]
                    QMessageBox.warning(
                        self,
                        "Multi-dimensional Image",
                        "Multi-dimensional image detected. Showing first frame/channel only."
                    )
            
            return image.astype(np.float64)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load image:\n{e}")
            return None
    
    def _on_pixel_preview(self):
        """Handle Pixel Intensities preview button click."""
        # Get selected file info
        file_info = self._get_selected_file_info()
        if not file_info:
            QMessageBox.warning(
                self,
                "No File Selected",
                "Please select a file from the list."
            )
            return
        
        directory, filename = file_info
        filepath = os.path.join(directory, filename)
        
        # Load image
        image = self._load_image(filepath)
        if image is None:
            return
        
        self._current_image = image
        
        # Generate and display figures
        self._update_pixel_preview()
    
    def _update_pixel_preview(self):
        """Update the pixel preview figures."""
        if self._current_image is None:
            return
        
        image = self._current_image
        
        # Clear previous figure
        self.figure.clear()
        
        # Create subplots
        ax1 = self.figure.add_subplot(121)
        ax2 = self.figure.add_subplot(122)
        
        # Heatmap (preserve aspect ratio)
        im = ax1.imshow(image, cmap='viridis', aspect='equal')
        ax1.set_title('Image Heatmap', fontsize=10)
        ax1.set_xlabel('X (pixels)', fontsize=9)
        ax1.set_ylabel('Y (pixels)', fontsize=9)
        self.figure.colorbar(im, ax=ax1, shrink=0.8)
        
        # Histogram
        flat_image = image.flatten()
        ax2.hist(flat_image, bins=256, color=Colors.ACCENT, alpha=0.7, edgecolor='none')
        ax2.set_title('Pixel Intensity Distribution', fontsize=10)
        ax2.set_xlabel('Pixel Value', fontsize=9)
        ax2.set_ylabel('Frequency', fontsize=9)
        
        # Apply scale
        if self.scale_combo.currentText() == "Logarithmic":
            ax2.set_yscale('log')
        else:
            ax2.set_yscale('linear')
        
        # Apply Y limits if set
        ymin = self.ymin_spin.value()
        ymax = self.ymax_spin.value()
        
        if ymax > ymin:
            ax2.set_ylim(ymin, ymax)
        
        # Adjust layout
        self.figure.tight_layout()
        
        # Refresh canvas
        self.canvas.draw()
    
    def _on_scale_changed(self, index: int):
        """Handle Y-axis scale change."""
        if self._current_image is not None:
            self._update_pixel_preview()
    
    def _on_ylim_changed(self, value: float):
        """Handle Y-axis limit change."""
        if self._current_image is not None:
            self._update_pixel_preview()
    
    def _on_auto_ylim(self):
        """Reset Y-axis limits to auto."""
        self.ymin_spin.setValue(0)
        self.ymax_spin.setValue(0)
        if self._current_image is not None:
            self._update_pixel_preview()
    
    def on_tab_selected(self):
        """Called when this tab becomes active."""
        # Refresh file list when tab is selected
        self.refresh_file_list()
    
    def get_data(self) -> dict:
        """Get the current tab data."""
        return {
            "pixel_intensities_enabled": self.pixel_intensities_toggle.isChecked(),
            "selected_file": self.file_list.currentItem().text() if self.file_list.currentItem() else None,
        }

