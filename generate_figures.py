"""
Figure Generation Script - Generates two-page PDF with threshold-masked heatmaps and fraction scatter plots.

This script creates figures for (STAT3)-Lemon and (NF-kB)-Lychee experiments.
"""

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('QtAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure

from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QListWidget, QListWidgetItem,
    QFileDialog, QMessageBox, QGroupBox, QLineEdit,
    QDialogButtonBox, QAbstractItemView, QProgressDialog
)
from PyQt6.QtCore import Qt


# Row labels for the figures
ROW_LABELS = ["Ctrl #1", "Ctrl #2", "TNFa #1", "TNFa #2", "LIF #1", "LIF #2"]

# Timepoint labels and patterns to search in filenames
TIMEPOINTS = ["0h", "2h", "4h", "6h", "24h", "48h"]
TIMEPOINT_PATTERNS = ["00h", "02h", "04h", "06h", "24h", "48h"]

# Default pickle file locations
DEFAULT_LEMON_PATH = r"F:\Klelia\Lemon"
DEFAULT_LYCHEE_PATH = r"F:\Klelia\Lychee"


class PickleFileSelector(QDialog):
    """Dialog for selecting pickle files for both figures."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Pickle Files")
        self.setMinimumWidth(600)
        self.setModal(True)
        
        self.lemon_path = None
        self.lychee_path = None
        
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Instructions
        instructions = QLabel(
            "Select the pickle files for each figure.\n"
            "The threshold values will be read from the 'Threshold' column in each file."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Lemon pickle file
        lemon_group = QGroupBox("(STAT3)-Lemon Figure")
        lemon_layout = QHBoxLayout(lemon_group)
        
        self.lemon_edit = QLineEdit()
        self.lemon_edit.setPlaceholderText("Select pickle file for Lemon...")
        self.lemon_edit.setReadOnly(True)
        lemon_layout.addWidget(self.lemon_edit, 1)
        
        lemon_browse = QPushButton("Browse...")
        lemon_browse.clicked.connect(lambda: self._browse_pickle("lemon"))
        lemon_layout.addWidget(lemon_browse)
        
        layout.addWidget(lemon_group)
        
        # Lychee pickle file
        lychee_group = QGroupBox("(NF-kB)-Lychee Figure")
        lychee_layout = QHBoxLayout(lychee_group)
        
        self.lychee_edit = QLineEdit()
        self.lychee_edit.setPlaceholderText("Select pickle file for Lychee...")
        self.lychee_edit.setReadOnly(True)
        lychee_layout.addWidget(self.lychee_edit, 1)
        
        lychee_browse = QPushButton("Browse...")
        lychee_browse.clicked.connect(lambda: self._browse_pickle("lychee"))
        lychee_layout.addWidget(lychee_browse)
        
        layout.addWidget(lychee_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _browse_pickle(self, which: str):
        """Browse for a pickle file."""
        if which == "lemon":
            default_dir = DEFAULT_LEMON_PATH if os.path.exists(DEFAULT_LEMON_PATH) else os.getcwd()
        else:
            default_dir = DEFAULT_LYCHEE_PATH if os.path.exists(DEFAULT_LYCHEE_PATH) else os.getcwd()
        
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            f"Select Pickle File for {which.capitalize()}",
            default_dir,
            "Pickle Files (*.pkl);;All Files (*)"
        )
        
        if filepath:
            if which == "lemon":
                self.lemon_path = filepath
                self.lemon_edit.setText(filepath)
            else:
                self.lychee_path = filepath
                self.lychee_edit.setText(filepath)
    
    def _validate_and_accept(self):
        """Validate selections and accept dialog."""
        if not self.lemon_path:
            QMessageBox.warning(self, "Missing File", "Please select a pickle file for the Lemon figure.")
            return
        if not self.lychee_path:
            QMessageBox.warning(self, "Missing File", "Please select a pickle file for the Lychee figure.")
            return
        
        self.accept()
    
    def get_paths(self) -> tuple[str, str]:
        """Return the selected pickle file paths."""
        return self.lemon_path, self.lychee_path


class GroupFileSelector(QDialog):
    """Dialog for selecting Group_ID and files for a single row."""
    
    def __init__(self, df: pd.DataFrame, row_label: str, figure_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Select Files for {row_label}")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self.setModal(True)
        
        self.df = df
        self.row_label = row_label
        self.figure_name = figure_name
        self.selected_files = {}  # timepoint -> filepath
        
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header
        header = QLabel(f"<b>{self.figure_name}</b> - Selecting files for <b>{self.row_label}</b>")
        header.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(header)
        
        # Group ID selection
        group_layout = QHBoxLayout()
        group_layout.addWidget(QLabel("Select Group_ID:"))
        
        self.group_combo = QComboBox()
        # Get unique Group_IDs
        group_ids = sorted(self.df["Group_ID"].unique())
        for gid in group_ids:
            # Get group name for this ID
            group_name = self.df[self.df["Group_ID"] == gid]["Group"].iloc[0]
            self.group_combo.addItem(f"{gid} - {group_name}", gid)
        
        self.group_combo.currentIndexChanged.connect(self._on_group_changed)
        group_layout.addWidget(self.group_combo)
        group_layout.addStretch()
        layout.addLayout(group_layout)
        
        # File list
        file_group = QGroupBox("Available Files (select 6 files, one for each timepoint)")
        file_layout = QVBoxLayout(file_group)
        
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        file_layout.addWidget(self.file_list)
        
        # Auto-select button
        auto_btn = QPushButton("Auto-Select by Timepoint Pattern")
        auto_btn.clicked.connect(self._auto_select)
        file_layout.addWidget(auto_btn)
        
        layout.addWidget(file_group)
        
        # Selected files display
        selected_group = QGroupBox("Selected Files by Timepoint")
        selected_layout = QVBoxLayout(selected_group)
        
        self.selected_labels = {}
        for tp in TIMEPOINTS:
            tp_layout = QHBoxLayout()
            tp_layout.addWidget(QLabel(f"{tp}:"))
            label = QLabel("(not selected)")
            label.setStyleSheet("color: gray;")
            self.selected_labels[tp] = label
            tp_layout.addWidget(label, 1)
            selected_layout.addLayout(tp_layout)
        
        layout.addWidget(selected_group)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._validate_and_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        # Connect selection change
        self.file_list.itemSelectionChanged.connect(self._on_selection_changed)
        
        # Initialize file list
        self._on_group_changed()
    
    def _on_group_changed(self):
        """Update file list when group changes."""
        self.file_list.clear()
        
        group_id = self.group_combo.currentData()
        if group_id is None:
            return
        
        # Get files for this group
        group_df = self.df[self.df["Group_ID"] == group_id]
        
        for _, row in group_df.iterrows():
            filename = row["Filename"]
            item = QListWidgetItem(filename)
            item.setData(Qt.ItemDataRole.UserRole, row.to_dict())
            self.file_list.addItem(item)
        
        # Reset selected files
        self.selected_files = {}
        self._update_selected_display()
    
    def _on_selection_changed(self):
        """Handle file selection change."""
        selected_items = self.file_list.selectedItems()
        
        # Try to match selected files to timepoints
        self.selected_files = {}
        
        for item in selected_items:
            filename = item.text()
            row_data = item.data(Qt.ItemDataRole.UserRole)
            
            # Try to determine timepoint from filename
            for tp, pattern in zip(TIMEPOINTS, TIMEPOINT_PATTERNS):
                if pattern in filename:
                    self.selected_files[tp] = row_data
                    break
        
        self._update_selected_display()
    
    def _update_selected_display(self):
        """Update the selected files display."""
        for tp in TIMEPOINTS:
            if tp in self.selected_files:
                filename = self.selected_files[tp]["Filename"]
                self.selected_labels[tp].setText(filename)
                self.selected_labels[tp].setStyleSheet("color: green;")
            else:
                self.selected_labels[tp].setText("(not selected)")
                self.selected_labels[tp].setStyleSheet("color: gray;")
    
    def _auto_select(self):
        """Auto-select files based on timepoint patterns."""
        # Clear current selection
        self.file_list.clearSelection()
        self.selected_files = {}
        
        # Try to find one file for each timepoint
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            filename = item.text()
            
            for tp, pattern in zip(TIMEPOINTS, TIMEPOINT_PATTERNS):
                if pattern in filename and tp not in self.selected_files:
                    item.setSelected(True)
                    row_data = item.data(Qt.ItemDataRole.UserRole)
                    self.selected_files[tp] = row_data
                    break
        
        self._update_selected_display()
        
        # Warn if not all timepoints found
        missing = [tp for tp in TIMEPOINTS if tp not in self.selected_files]
        if missing:
            QMessageBox.warning(
                self,
                "Missing Timepoints",
                f"Could not find files for timepoints: {', '.join(missing)}\n\n"
                "Please select them manually."
            )
    
    def _validate_and_accept(self):
        """Validate selections and accept dialog."""
        missing = [tp for tp in TIMEPOINTS if tp not in self.selected_files]
        
        if missing:
            reply = QMessageBox.warning(
                self,
                "Missing Timepoints",
                f"The following timepoints are not selected: {', '.join(missing)}\n\n"
                "Do you want to continue anyway? (Missing timepoints will show empty cells)",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        self.accept()
    
    def get_selected_files(self) -> dict:
        """Return the selected files by timepoint."""
        return self.selected_files


def load_image(filepath: str) -> np.ndarray | None:
    """
    Load an image from file.
    
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
        
    except Exception as e:
        print(f"Error loading image {filepath}: {e}")
        return None


def create_figure(figure_name: str, row_data: list[dict], threshold: float) -> Figure:
    """
    Create a figure with 6 rows of heatmaps and scatter plots.
    
    Args:
        figure_name: Name of the figure (e.g., "(STAT3)-Lemon")
        row_data: List of 6 dicts, each containing timepoint -> file_info mappings
        threshold: Threshold value for masking
        
    Returns:
        Matplotlib Figure object
    """
    # First pass: collect all fraction values to determine global y-axis max
    all_fractions = []
    for files_dict in row_data:
        for tp in TIMEPOINTS:
            if tp in files_dict:
                fraction = files_dict[tp].get("Fraction", np.nan)
                if not np.isnan(fraction):
                    all_fractions.append(fraction)
    
    # Determine global y-axis maximum for all scatter plots
    global_y_max = max(all_fractions) * 1.1 if all_fractions else 1.0
    
    # Create figure with appropriate size for A4 landscape
    fig = plt.figure(figsize=(16, 10), dpi=150)
    fig.suptitle(f"{figure_name}\nThreshold: {threshold:.1f}", fontsize=14, fontweight='bold', y=0.98)
    
    # Grid: 6 rows, 8 columns (1 label + 6 heatmaps + 1 scatter)
    # Using GridSpec for fine control
    from matplotlib.gridspec import GridSpec
    
    # Adjusted layout:
    # - top=0.88 to leave more room for the title/threshold text
    # - Added a gap column (index 7) between heatmaps and scatter plots
    # - width_ratios includes a small gap column (0.3) before the scatter plot
    gs = GridSpec(6, 9, figure=fig, 
                  width_ratios=[0.8, 1, 1, 1, 1, 1, 1, 0.3, 1.5],
                  left=0.02, right=0.98, top=0.88, bottom=0.05,
                  wspace=0.12, hspace=0.25)
    
    # Add column headers for timepoints
    for col_idx, tp in enumerate(TIMEPOINTS):
        ax = fig.add_subplot(gs[0, col_idx + 1])
        ax.text(0.5, 1.15, tp, ha='center', va='bottom', fontsize=10, fontweight='bold',
                transform=ax.transAxes)
        ax.axis('off')
    
    # Process each row
    for row_idx, (row_label, files_dict) in enumerate(zip(ROW_LABELS, row_data)):
        # Row label
        ax_label = fig.add_subplot(gs[row_idx, 0])
        ax_label.text(0.9, 0.5, row_label, ha='right', va='center', fontsize=10, fontweight='bold',
                      transform=ax_label.transAxes)
        ax_label.axis('off')
        
        # Collect fraction values for scatter plot
        fractions = []
        
        # Heatmaps for each timepoint
        for col_idx, tp in enumerate(TIMEPOINTS):
            ax = fig.add_subplot(gs[row_idx, col_idx + 1])
            
            if tp in files_dict:
                file_info = files_dict[tp]
                filepath = os.path.join(file_info["Directory"], file_info["Filename"])
                
                # Load image
                image = load_image(filepath)
                
                if image is not None:
                    # Apply threshold mask
                    mask = image < threshold
                    masked_image = np.ma.masked_where(mask, image)
                    
                    # Display heatmap
                    ax.imshow(masked_image, cmap='viridis', aspect='equal')
                    ax.imshow(mask, cmap='Greys', aspect='equal', alpha=mask.astype(float))
                else:
                    ax.text(0.5, 0.5, "Load\nFailed", ha='center', va='center',
                            fontsize=7, color='red', transform=ax.transAxes)
                
                # Get fraction value
                fractions.append(file_info.get("Fraction", np.nan))
            else:
                ax.text(0.5, 0.5, "No\nFile", ha='center', va='center',
                        fontsize=7, color='gray', transform=ax.transAxes)
                fractions.append(np.nan)
            
            ax.set_xticks([])
            ax.set_yticks([])
            ax.spines['top'].set_visible(True)
            ax.spines['right'].set_visible(True)
            ax.spines['bottom'].set_visible(True)
            ax.spines['left'].set_visible(True)
        
        # Scatter plot (column 8, after the gap column at 7)
        ax_scatter = fig.add_subplot(gs[row_idx, 8])
        
        # X positions: equal spacing (0, 1, 2, 3, 4, 5)
        x_positions = np.arange(len(TIMEPOINTS))
        
        # Plot scatter points
        valid_mask = ~np.isnan(fractions)
        ax_scatter.scatter(x_positions[valid_mask], np.array(fractions)[valid_mask], 
                          s=50, c='#3498DB', edgecolors='black', linewidths=0.5, zorder=3)
        
        # Connect points with lines
        if np.sum(valid_mask) > 1:
            ax_scatter.plot(x_positions[valid_mask], np.array(fractions)[valid_mask],
                           color='#3498DB', linewidth=1, alpha=0.7, zorder=2)
        
        # Add dotted vertical lines between 6h-24h (between index 3 and 4) and 24h-48h (between index 4 and 5)
        ax_scatter.axvline(x=3.5, color='gray', linestyle=':', linewidth=1, alpha=0.7)
        ax_scatter.axvline(x=4.5, color='gray', linestyle=':', linewidth=1, alpha=0.7)
        
        # Configure scatter plot
        ax_scatter.set_xlim(-0.5, 5.5)
        ax_scatter.set_xticks(x_positions)
        ax_scatter.set_xticklabels(TIMEPOINTS, fontsize=7)
        ax_scatter.set_ylabel("Fraction", fontsize=8)
        ax_scatter.tick_params(axis='y', labelsize=7)
        
        # Set y-axis to global maximum (same for all rows in the figure)
        ax_scatter.set_ylim(0, global_y_max)
        
        # Add grid
        ax_scatter.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
        ax_scatter.set_axisbelow(True)
    
    return fig


def regenerate_from_pickle(selection_pickle_path: str):
    """
    Regenerate figures from a saved selections pickle file.
    
    Args:
        selection_pickle_path: Path to the figure_selections.pkl file
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Load selection data
    try:
        selection_data = pd.read_pickle(selection_pickle_path)
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Failed to load selection pickle:\n{e}")
        return
    
    # Validate structure
    if "lemon" not in selection_data or "lychee" not in selection_data:
        QMessageBox.critical(None, "Error", "Invalid selection pickle format.")
        return
    
    # Prepare figure data from selections
    figures_data = []
    
    for fig_key in ["lemon", "lychee"]:
        fig_info = selection_data[fig_key]
        row_data = []
        
        for row_label in ROW_LABELS:
            if row_label in fig_info["selections"]:
                row_data.append(fig_info["selections"][row_label])
            else:
                row_data.append({})
        
        figures_data.append({
            "name": fig_info["figure_name"],
            "row_data": row_data,
            "threshold": fig_info["threshold"],
            "pickle_path": fig_info["source_pickle"]
        })
    
    # Create progress dialog
    progress = QProgressDialog("Regenerating figures...", None, 0, 3)
    progress.setWindowTitle("Regenerating Figures")
    progress.setWindowModality(Qt.WindowModality.WindowModal)
    progress.setMinimumDuration(0)
    progress.setValue(0)
    
    # Create figures
    progress.setLabelText("Creating Lemon figure...")
    lemon_fig = create_figure(
        figures_data[0]["name"],
        figures_data[0]["row_data"],
        figures_data[0]["threshold"]
    )
    progress.setValue(1)
    
    progress.setLabelText("Creating Lychee figure...")
    lychee_fig = create_figure(
        figures_data[1]["name"],
        figures_data[1]["row_data"],
        figures_data[1]["threshold"]
    )
    progress.setValue(2)
    
    # Determine output directory (same as selection pickle location)
    figures_dir = os.path.dirname(selection_pickle_path)
    
    progress.setLabelText("Saving figures...")
    
    # Save as PDF (multi-page)
    pdf_path = os.path.join(figures_dir, "combined_figures.pdf")
    with PdfPages(pdf_path) as pdf:
        pdf.savefig(lemon_fig, bbox_inches='tight')
        pdf.savefig(lychee_fig, bbox_inches='tight')
    
    # Save as individual PNGs
    lemon_fig.savefig(os.path.join(figures_dir, "STAT3_Lemon.png"), 
                      dpi=300, bbox_inches='tight', facecolor='white')
    lychee_fig.savefig(os.path.join(figures_dir, "NF-kB_Lychee.png"), 
                       dpi=300, bbox_inches='tight', facecolor='white')
    
    # Save as individual SVGs
    lemon_fig.savefig(os.path.join(figures_dir, "STAT3_Lemon.svg"), 
                      bbox_inches='tight', facecolor='white')
    lychee_fig.savefig(os.path.join(figures_dir, "NF-kB_Lychee.svg"), 
                       bbox_inches='tight', facecolor='white')
    
    progress.setValue(3)
    
    # Close figures
    plt.close(lemon_fig)
    plt.close(lychee_fig)
    
    # Show completion message
    QMessageBox.information(
        None,
        "Complete",
        f"Figures regenerated successfully!\n\n"
        f"Saved to: {figures_dir}\n\n"
        f"Files created:\n"
        f"  - combined_figures.pdf (2-page PDF)\n"
        f"  - STAT3_Lemon.png\n"
        f"  - STAT3_Lemon.svg\n"
        f"  - NF-kB_Lychee.png\n"
        f"  - NF-kB_Lychee.svg"
    )


def main():
    """Main function to run the figure generation script."""
    app = QApplication(sys.argv)
    
    # Check for command line argument to regenerate from pickle
    if len(sys.argv) > 1:
        selection_pickle_path = sys.argv[1]
        if os.path.exists(selection_pickle_path) and selection_pickle_path.endswith('.pkl'):
            regenerate_from_pickle(selection_pickle_path)
            return
        else:
            print(f"Invalid pickle file path: {selection_pickle_path}")
            return
    
    # Step 1: Select pickle files
    pickle_selector = PickleFileSelector()
    if pickle_selector.exec() != QDialog.DialogCode.Accepted:
        print("Cancelled by user.")
        return
    
    lemon_path, lychee_path = pickle_selector.get_paths()
    
    # Load pickle files
    try:
        lemon_df = pd.read_pickle(lemon_path)
        lychee_df = pd.read_pickle(lychee_path)
    except Exception as e:
        QMessageBox.critical(None, "Error", f"Failed to load pickle files:\n{e}")
        return
    
    # Validate required columns
    required_cols = ["Filename", "Directory", "Group", "Group_ID", "Threshold", "Fraction"]
    for name, df in [("Lemon", lemon_df), ("Lychee", lychee_df)]:
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            QMessageBox.critical(
                None, "Error",
                f"Pickle file for {name} is missing required columns: {', '.join(missing)}"
            )
            return
    
    # Get threshold values (should be constant within each file)
    lemon_threshold = lemon_df["Threshold"].iloc[0]
    lychee_threshold = lychee_df["Threshold"].iloc[0]
    
    # Collect data for both figures
    figures_data = []
    
    for figure_name, df, threshold, pickle_path in [
        ("(STAT3)-Lemon", lemon_df, lemon_threshold, lemon_path),
        ("(NF-kB)-Lychee", lychee_df, lychee_threshold, lychee_path)
    ]:
        row_data = []
        
        for row_label in ROW_LABELS:
            selector = GroupFileSelector(df, row_label, figure_name)
            
            if selector.exec() != QDialog.DialogCode.Accepted:
                print(f"Cancelled at {figure_name} - {row_label}")
                return
            
            row_data.append(selector.get_selected_files())
        
        figures_data.append({
            "name": figure_name,
            "row_data": row_data,
            "threshold": threshold,
            "pickle_path": pickle_path
        })
    
    # Create progress dialog
    progress = QProgressDialog("Generating figures...", None, 0, 3)
    progress.setWindowTitle("Generating Figures")
    progress.setWindowModality(Qt.WindowModality.WindowModal)
    progress.setMinimumDuration(0)
    progress.setValue(0)
    
    # Create figures
    progress.setLabelText("Creating Lemon figure...")
    lemon_fig = create_figure(
        figures_data[0]["name"],
        figures_data[0]["row_data"],
        figures_data[0]["threshold"]
    )
    progress.setValue(1)
    
    progress.setLabelText("Creating Lychee figure...")
    lychee_fig = create_figure(
        figures_data[1]["name"],
        figures_data[1]["row_data"],
        figures_data[1]["threshold"]
    )
    progress.setValue(2)
    
    # Determine output directory (same as first pickle file location)
    output_base = os.path.dirname(lemon_path)
    figures_dir = os.path.join(output_base, "figures")
    os.makedirs(figures_dir, exist_ok=True)
    
    progress.setLabelText("Saving figures...")
    
    # Save as PDF (multi-page)
    pdf_path = os.path.join(figures_dir, "combined_figures.pdf")
    with PdfPages(pdf_path) as pdf:
        pdf.savefig(lemon_fig, bbox_inches='tight')
        pdf.savefig(lychee_fig, bbox_inches='tight')
    
    # Save as individual PNGs
    lemon_fig.savefig(os.path.join(figures_dir, "STAT3_Lemon.png"), 
                      dpi=300, bbox_inches='tight', facecolor='white')
    lychee_fig.savefig(os.path.join(figures_dir, "NF-kB_Lychee.png"), 
                       dpi=300, bbox_inches='tight', facecolor='white')
    
    # Save as individual SVGs
    lemon_fig.savefig(os.path.join(figures_dir, "STAT3_Lemon.svg"), 
                      bbox_inches='tight', facecolor='white')
    lychee_fig.savefig(os.path.join(figures_dir, "NF-kB_Lychee.svg"), 
                       bbox_inches='tight', facecolor='white')
    
    # Save selection data as pickle for reproducibility
    selection_data = {
        "lemon": {
            "source_pickle": lemon_path,
            "figure_name": figures_data[0]["name"],
            "threshold": figures_data[0]["threshold"],
            "selections": {}
        },
        "lychee": {
            "source_pickle": lychee_path,
            "figure_name": figures_data[1]["name"],
            "threshold": figures_data[1]["threshold"],
            "selections": {}
        }
    }
    
    # Store selections for each row
    for fig_key, fig_data in [("lemon", figures_data[0]), ("lychee", figures_data[1])]:
        for row_label, files_dict in zip(ROW_LABELS, fig_data["row_data"]):
            selection_data[fig_key]["selections"][row_label] = {
                tp: {
                    "Filename": info["Filename"],
                    "Directory": info["Directory"],
                    "Group": info.get("Group", ""),
                    "Group_ID": info.get("Group_ID", 0),
                    "Fraction": info.get("Fraction", np.nan),
                    "Threshold": info.get("Threshold", np.nan)
                }
                for tp, info in files_dict.items()
            }
    
    # Save selection pickle
    selection_pickle_path = os.path.join(figures_dir, "figure_selections.pkl")
    pd.to_pickle(selection_data, selection_pickle_path)
    
    progress.setValue(3)
    
    # Close figures
    plt.close(lemon_fig)
    plt.close(lychee_fig)
    
    # Show completion message
    QMessageBox.information(
        None,
        "Complete",
        f"Figures generated successfully!\n\n"
        f"Saved to: {figures_dir}\n\n"
        f"Files created:\n"
        f"  - combined_figures.pdf (2-page PDF)\n"
        f"  - STAT3_Lemon.png\n"
        f"  - STAT3_Lemon.svg\n"
        f"  - NF-kB_Lychee.png\n"
        f"  - NF-kB_Lychee.svg\n"
        f"  - figure_selections.pkl (for reproducibility)"
    )


if __name__ == "__main__":
    main()
