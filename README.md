# Cell Image Analyzer

A GUI-based application for analyzing batches of cell images obtained under various experimental conditions. Built with PyQt6 and matplotlib for visualization.

## Table of Contents

- [Installation](#installation)
- [Running the Application](#running-the-application)
- [User Guide](#user-guide)
  - [Input Workspace](#1-input-workspace)
  - [Analysis Workspace](#2-analysis-workspace)
  - [Output Workspace](#3-output-workspace)

---

## Installation

### Prerequisites

- Python 3.10 or higher
- Git

### Clone the Repository

```bash
git clone https://github.com/yourusername/Cell_Image_Analyzer.git
cd Cell_Image_Analyzer
```

### Set Up Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Running the Application

With the virtual environment activated, run:

```bash
python main.py
```

---

## User Guide

The application consists of three main workspaces, accessible via the navigation panel on the left side. Work through them in order: **Input → Analysis → Output**.

---

### 1. Input Workspace

The Input workspace is where you select and organize your image files.

#### File Import Tab

- **Directory Selection**: Browse and select the folder containing your image files
- **File Filtering**: Filter files by extension (e.g., `.tif`, `.tiff`, `.nd2`)
- **File Selection**: Select individual files or use "Select All" to include all filtered files

#### Groups Tab

- **Grouping**: Organize selected files into groups based on naming patterns
- **Group Preview**: View how files are distributed across groups
- **Group Management**: Create, rename, or delete groups

<img width="1283" height="830" alt="image" src="https://github.com/user-attachments/assets/c720e974-6c01-4e86-ba2a-69ffcbc3d45e" />


---

### 2. Analysis Workspace

The Analysis workspace handles data management and image processing.

#### Pickle DataFile Tab

- **Start New**: Create a new pickle data file from selected files in the Input workspace
  - Automatically extracts filenames, directories, and group information
  - Prompts for save location
- **Load Existing**: Load a previously saved pickle file
- **Pickle Display**: View the DataFrame contents in a scrollable table
- **Sort by Groups**: Toggle to sort entries by group assignment
- **Save**: Save changes to the current pickle file

#### Raw Processing Tab

- **Fluorescence Intensities Section**:
  - **Pixel Intensities Toggle**: Enable pixel intensity analysis
  - **Background Threshold Toggle**: Enable threshold-based background subtraction
    - Enter threshold value directly or drag the red line on the histogram
    - Preview updates automatically with 300ms debounce
  - **Preview Button**: Generate preview of selected file

- **File for Preview Pane**:
  - Lists all files from the pickle data
  - Auto-updates preview when selection changes (400ms debounce)

- **Preview Figures Pane**:
  - **Image Heatmap**: Displays the image with threshold masking (pixels below threshold shown in black)
  - **Pixel Intensity Distribution**: Histogram of pixel values with threshold line
  - **Y-axis Controls**: Linear/Logarithmic scale, manual Y min/max, Auto button

- **Process Button**: Process all files in the pickle with the current threshold
  - Adds columns to pickle file:
    - `Threshold`: The threshold value used
    - `Fraction`: Fraction of pixels above threshold
    - `Mean Value`: Mean value of pixels above threshold
  - Shows progress dialog during processing
  - Handles existing columns (Cancel/Overwrite/Save As options)

---

### 3. Output Workspace

The Output workspace generates visual reports and exports.

#### Settings Pane

- **Pickle File**: Display current pickle file path with Browse button to load different file
- **File Selection**: Toggle between "Groups" and "Singles" mode
  - Groups: Generate sheets per group
  - Singles: (Not yet implemented)
- **Composite Toggle**: ON (locked) - composite visualizations enabled
- **Content Toggles** (all locked ON):
  - Heatmaps
  - Intensity Distributions
  - Fractions
- **Display Options**:
  - **Log-scale**: Toggle logarithmic Y-axis for intensity distributions
  - **Norm**: Toggle normalization (each histogram peak = 1.0)
- **Export As...**: Export sheets to PNG or SVG files

#### File Overview Pane

- Lists all groups with toggle checkboxes
- Groups are OFF by default - select groups to generate their sheets
- Only selected groups are rendered in the preview

#### Preview Pane

- **Scrollable sheet view**: Navigate through sheets (one per group)
- **Sheet Layout** (A4 landscape proportions):
  - **Header**: Group name and ID
  - **Left side (~55%)**: Heatmaps of all files in grid layout
    - Threshold masking applied
    - Adaptive grid arrangement
  - **Upper right**: Overlaid intensity distributions
    - Only pixels above threshold
    - Color-coded per file
    - Optional log-scale and normalization
  - **Lower right**: Fraction bar chart
    - One bar per file
    - Colors match intensity distribution lines
    - Auto-scaled Y-axis

#### Export Functionality

- **Export Dialog**:
  - Select destination directory
  - Enter folder name (defaults to pickle filename)
  - Choose format: PNG (300 DPI) or SVG
- **Export Output**:
  - Creates folder at destination
  - One file per sheet: `{GroupName}_{GroupID}.{format}`
  - Progress dialog during export

---

## File Format Support

- **TIFF/TIF**: Standard microscopy format
- **ND2**: Nikon microscopy format (requires nd2reader)
- **PNG, JPEG, etc.**: Via PIL/Pillow

---

## Dependencies

Key packages:
- **PyQt6**: GUI framework
- **matplotlib**: Visualization and plotting
- **pandas**: Data management
- **numpy**: Numerical operations
- **tifffile**: TIFF file support
- **nd2reader**: Nikon ND2 file support
- **Pillow**: General image format support

See `requirements.txt` for complete list with versions.

---

## License

See [LICENSE](LICENSE) file for details.
