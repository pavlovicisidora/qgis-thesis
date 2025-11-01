# OSM POI Downloader - QGIS Plugin

A QGIS plugin for downloading and visualizing Points of Interest (POI) data from OpenStreetMap using the Overpass API.

## Overview

This plugin allows users to quickly download POI data from OpenStreetMap by drawing a bounding box on the map and selecting one or more POI categories. The downloaded data is automatically displayed as styled layers in QGIS and can be exported to GeoJSON or CSV formats.

## Features

### Core Functionality
- **Interactive Area Selection**: Draw a rectangle directly on the QGIS map canvas to define your search area
- **Multiple POI Categories**: Support for 13 common POI types:
  - Restaurant
  - Cafe
  - Hospital
  - School
  - Bank
  - ATM
  - Pharmacy
  - Gas Station
  - Supermarket
  - Mall
  - Bus Station
  - Train Station
  - Hotel

### Advanced Features
- **Multi-Category Download**: Select and download multiple POI categories simultaneously
- **Automatic Styling**: Each POI category is displayed with a distinct color for easy visual identification
- **Statistical Analysis**: Automatic calculation of:
  - Number of POIs found
  - Area covered (km²)
  - POI density (POIs per km²)
  - Geographic bounds
- **Data Export**: Export downloaded POI data to:
  - GeoJSON format (for use in web maps and other GIS software)
  - CSV format (for use in spreadsheets and databases)
- **Batch Export**: Export all downloaded layers at once or select specific layers to export

## Installation

### Requirements
- QGIS 3.0 or higher (tested on QGIS 3.40)
- Internet connection (for accessing OpenStreetMap Overpass API)
- Python 3.9 or higher

### Installing the Plugin

#### Method 1: From Source (for development/testing)

1. Clone or download this repository
2. Copy the `osm_poi_downloader` folder to your QGIS plugins directory:
   - **Windows**: `C:\Users\<YourName>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\`
   - **Linux**: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - **Mac**: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
3. Restart QGIS
4. Enable the plugin:
   - Go to `Plugins` → `Manage and Install Plugins`
   - Find "OSM POI Downloader" in the Installed tab
   - Check the box to activate it

#### Method 2: Via Plugin Repository (when published)
1. In QGIS, go to `Plugins` → `Manage and Install Plugins`
2. Search for "OSM POI Downloader"
3. Click `Install Plugin`

## Usage

### Basic Workflow

1. **Open the Plugin**
   - Click the plugin icon in the toolbar, or
   - Go to `Plugins` → `OSM POI Downloader` → `Download OSM POIs`

2. **Select POI Categories**
   - Check one or more POI categories you want to download
   - You can select multiple categories to download them all at once

3. **Define Search Area**
   - Click `Select area on map`
   - The dialog will hide and your cursor will become a crosshair
   - Click and drag on the map to draw a rectangle
   - Release the mouse to confirm the selection
   - The dialog will reappear with the selected coordinates

4. **Download POIs**
   - Click `Download POIs`
   - Progress bar shows download status for each category
   - Upon completion, new layers appear in the Layers panel
   - Statistics panel shows analysis of the downloaded data

5. **Export Data (Optional)**
   - Select export format (GeoJSON or CSV) from the dropdown
   - Click `Export Layer`
   - Choose to export all layers or select specific ones
   - Select save location

### Tips for Best Results

- **Area Size**: For best performance, keep your search area under 25 km²
- **Dense Areas**: In city centers, consider smaller areas or fewer categories to avoid timeouts
- **No Results**: If no POIs are found, try:
  - A larger area
  - Different categories (some POI types may not be mapped in all regions)
  - A different location

## Screenshots

### Main Interface
![Plugin Dialog](docs/screenshots/main_interface.png)

### Results with Statistics
![Results Display](docs/screenshots/results_statistics.png)

### Multiple Layers
![Multiple Categories](docs/screenshots/multiple_layers.png)

## Technical Details

### Architecture

The plugin consists of several modular components:

- **`osm_poi_downloader.py`**: Main plugin class and QGIS integration
- **`osm_poi_downloader_dialog.py`**: User interface logic and workflow coordination
- **`map_tool_select_area.py`**: Custom map tool for interactive rectangle selection
- **`overpass_api.py`**: Overpass API client with query builder and response parser
- **`poi_layer_creator.py`**: QGIS layer creation and styling
- **`exporter.py`**: Data export functionality (GeoJSON, CSV)
- **`statistics_calculator.py`**: Geographic calculations and statistics

### Data Source

All POI data comes from **OpenStreetMap** via the **Overpass API**:
- Data is licensed under the [Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/)
- Contributors: OpenStreetMap community
- Data quality varies by region based on mapping activity

### API Usage

This plugin uses the public Overpass API endpoint (`https://overpass-api.de/api/interpreter`):
- Queries timeout after 25 seconds
- Fair use policy applies
- For heavy usage, consider running your own Overpass instance

## Limitations

- **Area Size**: Very large areas (>50 km²) may timeout or return incomplete results
- **Rate Limits**: Excessive queries may be temporarily throttled by the Overpass API
- **Data Coverage**: POI availability depends on OpenStreetMap mapping completeness in the region
- **Coordinate System**: Works in any CRS but converts to WGS84 (EPSG:4326) for API queries
- **Network Dependency**: Requires active internet connection

## Troubleshooting

### Common Issues

**Problem**: Plugin doesn't appear in the Plugins menu
- **Solution**: Make sure the plugin folder is in the correct location and QGIS was restarted

**Problem**: "Request timed out" error
- **Solution**: Either the area is too large or the API is busy. Try again with a smaller area

**Problem**: No POIs found in an urban area
- **Solution**: The selected category may not be well-mapped in that region. Try different categories

**Problem**: Export button is disabled
- **Solution**: Download POIs first before attempting to export

## Development

### Project Structure
```
osm_poi_downloader/
├── __init__.py                          # Plugin entry point
├── metadata.txt                         # Plugin metadata
├── osm_poi_downloader.py               # Main plugin class
├── osm_poi_downloader_dialog.py        # Dialog logic
├── osm_poi_downloader_dialog_base.ui   # UI layout (Qt Designer)
├── osm_poi_downloader_dialog_base.py   # Generated from .ui file
├── map_tool_select_area.py             # Map selection tool
├── overpass_api.py                     # API client
├── poi_layer_creator.py                # Layer creation
├── exporter.py                         # Export functionality
├── statistics_calculator.py            # Statistics calculations
├── resources.py                        # Qt resources (icons)
└── icon.png                            # Plugin icon
```

### Building from Source

1. Clone the repository
2. Make modifications to the code
3. If UI changes are made:
   ```bash
   pyuic5 -o osm_poi_downloader_dialog_base.py osm_poi_downloader_dialog_base.ui
   ```
4. If resources change:
   ```bash
   pyrcc5 -o resources.py resources.qrc
   ```

## Author

**Isidora Pavlović**
- Email: isidorapavlovic0@gmail.com
- GitHub: [pavlovicisidora](https://github.com/pavlovicisidora/qgis-thesis)

## Acknowledgments

- OpenStreetMap contributors for providing the data
- Overpass API developers for the query interface
- QGIS development team for the excellent platform and PyQGIS API
