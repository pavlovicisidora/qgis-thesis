# -*- coding: utf-8 -*-
import os

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
from qgis.PyQt.QtWidgets import QMessageBox
from qgis.PyQt.QtWidgets import QFileDialog
from .exporter import LayerExporter
from .poi_layer_creator import PoiLayerCreator
from .map_tool_select_area import MapToolSelectArea
from .overpass_api import OverpassAPI

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'osm_poi_downloader_dialog_base.ui'))


class OsmPoiDownloaderDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, canvas, parent=None):
        """Constructor."""
        super(OsmPoiDownloaderDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.canvas = canvas
        
        self.bbox = None
        
        self.mapTool = MapToolSelectArea(self.canvas)
        self.mapTool.areaSelected.connect(self.on_area_selected)
        
        self.progressBar.setVisible(False)
        self.pushButton_download.setEnabled(False)
        self.label_status.setText("Status: Ready")
        
        self.pushButton_selectArea.clicked.connect(self.select_area)
        self.pushButton_download.clicked.connect(self.download_pois)
        self.current_layer = None

        self.pushButton_export.clicked.connect(self.export_layer)
        
    def select_area(self):
        """Let user select a bounding box on the map."""
        self.label_status.setText("Status: Click and drag on map to select area...")
        self.canvas.setMapTool(self.mapTool)
        self.hide()
        
    def on_area_selected(self, rectangle):
        """
        Called when user finishes drawing the rectangle.
        Args:
            rectangle: QgsRectangle in map coordinates
        """    
        self.show()
        self.canvas.unsetMapTool(self.mapTool)
        
        source_crs = self.canvas.mapSettings().destinationCrs()
        dest_crs = QgsCoordinateReferenceSystem("EPSG:4326")
        transform = QgsCoordinateTransform(source_crs, dest_crs, QgsProject.instance())
        
        rect_wgs84 = transform.transformBoundingBox(rectangle)
        
        self.bbox = (
            rect_wgs84.yMinimum(),
            rect_wgs84.xMinimum(),
            rect_wgs84.yMaximum(),
            rect_wgs84.xMaximum()
        )
        
        self.label_selectedArea.setText(
            f"Selected Area: {rect_wgs84.yMinimum():.4f}, {rect_wgs84.xMinimum():.4f} to "
            f"{rect_wgs84.yMaximum():.4f}, {rect_wgs84.xMaximum():.4f}"
        )
        self.pushButton_download.setEnabled(True)
        self.label_status.setText("Status: Area selected. Ready to download.")
        
    def download_pois(self):
        """Download POIs from Overpass API."""
        if not self.bbox:
            QMessageBox.warning(self, "No Area Selected", "Please select an area on the map first.")
            return
        
        category = self.comboBox_category.currentText()
        
        # Update UI
        self.label_status.setText(f"Status: Downloading {category} POIs...")
        self.progressBar.setVisible(True)
        self.progressBar.setValue(10)
        self.pushButton_download.setEnabled(False)
        self.pushButton_export.setEnabled(False)
        
        try:
            # Query Overpass API
            self.progressBar.setValue(30)
            data = OverpassAPI.query_overpass(self.bbox, category)
            
            self.progressBar.setValue(60)
            features = OverpassAPI.parse_features(data)
            
            if not features:
                QMessageBox.information(
                    self,
                    "No Results",
                    f"No {category} POIs found in the selected area."
                )
                self.reset_ui()
                return
            
            self.progressBar.setValue(80)
            layer_name = f"OSM {category.title()} ({len(features)} points)"
            layer = PoiLayerCreator.create_layer(features, layer_name, category)
            
            if layer:
                PoiLayerCreator.add_layer_to_project(layer)
                self.current_layer = layer

                self.pushButton_export.setEnabled(True)
                self.progressBar.setValue(100)
                
                self.label_status.setText(f"Status: Downloaded {len(features)} {category} POIs")
                QMessageBox.information(
                    self,
                    "Success",
                    f"Downloaded {len(features)} {category} POIs.\nLayer added to map."
                )
            else:
                raise Exception("Failed to create layer")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to download POIs:\n{str(e)}"
            )
            self.label_status.setText(f"Status: Error - {str(e)}")
        
        finally:
            self.reset_ui()

    def reset_ui(self):
        """Reset UI to ready state."""
        self.progressBar.setVisible(False)
        self.progressBar.setValue(0)
        self.pushButton_download.setEnabled(True)
        
    def export_layer(self):
        """Export the current layer to selected format."""
        if not self.current_layer:
            QMessageBox.warning(self, "No Layer", "No layer to export. Download POIs first.")
            return
        
        export_format = self.comboBox_exportFormat.currentText()
        
        if export_format == "GeoJSON":
            filter_str = "GeoJSON Files (*.geojson);;All Files (*)"
            default_ext = ".geojson"
        elif export_format == "CSV":
            filter_str = "CSV Files (*.csv);;All Files (*)"
            default_ext = ".csv"
        else:
            QMessageBox.warning(self, "Invalid Format", "Please select a valid export format.")
            return
        
        # Open file dialog
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            f"Save {export_format} File",
            "",
            filter_str
        )
        
        if not filepath:
            return
        
        if not filepath.lower().endswith(default_ext):
            filepath += default_ext
        
        self.label_status.setText(f"Status: Exporting to {export_format}...")
        self.pushButton_export.setEnabled(False)
        
        if export_format == "GeoJSON":
            success, error_msg = LayerExporter.export_to_geojson(self.current_layer, filepath)
        else: 
            success, error_msg = LayerExporter.export_to_csv(self.current_layer, filepath)
        
        if success:
            feature_count = LayerExporter.get_feature_count(self.current_layer)
            QMessageBox.information(
                self,
                "Export Successful",
                f"Exported {feature_count} features to {export_format}:\n{filepath}"
            )
            self.label_status.setText(f"Status: Exported to {os.path.basename(filepath)}")
        else:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Could not export layer:\n{error_msg}"
            )
            self.label_status.setText("Status: Export failed")
        
        self.pushButton_export.setEnabled(True)
