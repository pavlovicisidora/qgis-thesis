# -*- coding: utf-8 -*-
import os

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.core import QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsProject
from qgis.PyQt.QtWidgets import QMessageBox, QFileDialog, QInputDialog
from .exporter import LayerExporter
from .poi_layer_creator import PoiLayerCreator
from .map_tool_select_area import MapToolSelectArea
from .overpass_api import OverpassAPI
from .statistics_calculator import StatisticsCalculator
from .map_exporter import MapExporter

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
        self.groupBox_stats.setVisible(False)
        self.label_status.setText("Status: Ready")
        
        self.pushButton_selectArea.clicked.connect(self.select_area)
        self.pushButton_download.clicked.connect(self.download_pois)
        self.current_layers = []

        self.pushButton_export.clicked.connect(self.export_layer)
        self.pushButton_exportMap.clicked.connect(self.export_map_with_legend)
        
    def get_selected_categories(self):
        """
        Get list of selected POI categories from checkboxes.
        
        Returns:
            List of category name strings
        """
        categories = []
        
        risk_zone_mapping = {
            self.checkBox_factory: 'factory',
            self.checkBox_gasStation: 'gas station',
            self.checkBox_powerPlant: 'power plant',
            self.checkBox_powerSubstation: 'power substation',
            self.checkBox_railwayStation: 'railway station',
            self.checkBox_railwayHalt: 'railway halt',
            self.checkBox_waterworks: 'waterworks',
            self.checkBox_wastewaterPlant: 'wastewater plant',
            self.checkBox_industrialZone: 'industrial zone',
        }
        
        vulnerable_pop_mapping = {
            self.checkBox_school: 'school',
            self.checkBox_kindergarten: 'kindergarten',
            self.checkBox_hospital: 'hospital',
            self.checkBox_clinic: 'clinic',
            self.checkBox_nursingHome: 'nursing home',
            self.checkBox_socialFacility: 'social facility',
            self.checkBox_childcare: 'childcare',
            self.checkBox_communityCentre: 'community centre',
        }
        
        checkbox_mapping = {**risk_zone_mapping, **vulnerable_pop_mapping}

        for checkbox, category in checkbox_mapping.items():
            if checkbox.isChecked():
                categories.append(category)
        
        return categories
    
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
        """Download POIs from Overpass API for selected categories."""
        if not self.bbox:
            QMessageBox.warning(self, "No Area Selected", "Please select an area on the map first.")
            return
        
        selected_categories = self.get_selected_categories()
        
        if not selected_categories:
            QMessageBox.warning(
                self,
                "No Categories Selected",
                "Please select at least one POI category."
            )
            return
        
        self.pushButton_download.setEnabled(False)
        self.pushButton_export.setEnabled(False)
        self.groupBox_stats.setVisible(False)
        
        self.progressBar.setVisible(True)
        self.progressBar.setValue(0)
        
        created_layers = []
        total_features = 0
        
        try:
            use_batch = len(selected_categories) >= 3
            
            if use_batch:
                self.label_status.setText(f"Status: Downloading all categories in batch...")
                self.progressBar.setValue(10)
                
                data = OverpassAPI.query_overpass_batch(self.bbox, selected_categories)
                categorized_features = OverpassAPI.parse_batch_features(data)
                
                self.progressBar.setValue(60)
                
                progress_per_layer = 30 // len(categorized_features) if categorized_features else 0
                current_progress = 60
                
                for category, features in categorized_features.items():
                    if features:
                        layer_name = f"OSM {category.title()} ({len(features)} points)"
                        layer = PoiLayerCreator.create_layer(features, layer_name, category)
                        
                        if layer:
                            PoiLayerCreator.add_layer_to_project(layer)
                            created_layers.append((category, layer, len(features)))
                            total_features += len(features)
                    
                    current_progress += progress_per_layer
                    self.progressBar.setValue(current_progress)
                
            else:
                import time
                
                progress_per_category = 80 // len(selected_categories)
                current_progress = 10
                
                for i, category in enumerate(selected_categories):
                    self.label_status.setText(f"Status: Downloading {category} ({i+1}/{len(selected_categories)})...")
                    self.progressBar.setValue(current_progress)
                    
                    if i > 0:
                        time.sleep(2)
                    
                    data = OverpassAPI.query_overpass(self.bbox, category)
                    features = OverpassAPI.parse_features(data)
                    
                    if features:
                        layer_name = f"OSM {category.title()} ({len(features)} points)"
                        layer = PoiLayerCreator.create_layer(features, layer_name, category)
                        
                        if layer:
                            PoiLayerCreator.add_layer_to_project(layer)
                            created_layers.append((category, layer, len(features)))
                            total_features += len(features)
                    
                    current_progress += progress_per_category
                    self.progressBar.setValue(current_progress)
            
            self.progressBar.setValue(100)
            
            if not created_layers:
                QMessageBox.information(
                    self,
                    "No Results",
                    f"No POIs found for selected categories in this area."
                )
                return
            
            self.current_layers = [(cat, layer) for cat, layer, count in created_layers]
            self.pushButton_export.setEnabled(True)
            
            layer_summary = "\n".join([f"  • {cat.title()}: {count} POIs" 
                                    for cat, layer, count in created_layers])
            
            stats_text = StatisticsCalculator.format_statistics(
                total_features,
                self.bbox,
                f"{len(selected_categories)} categories"
            )
            self.label_statistics.setText(stats_text)
            self.groupBox_stats.setVisible(True)
            
            self.label_status.setText(f"Status: Downloaded {total_features} POIs across {len(created_layers)} categories")
            
            QMessageBox.information(
                self,
                "Success",
                f"Downloaded {total_features} POIs in {len(created_layers)} layer(s):\n\n{layer_summary}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to download POIs:\n{str(e)}"
            )
            self.label_status.setText(f"Status: Error - {str(e)}")
        
        finally:
            self.reset_ui

    def reset_ui(self):
        """Reset UI to ready state."""
        self.progressBar.setVisible(False)
        self.progressBar.setValue(0)
        self.pushButton_download.setEnabled(True)

    def export_layer(self):
        """Export downloaded layers to selected format."""
        if not self.current_layers:
            QMessageBox.warning(self, "No Layers", "No layers to export. Download POIs first.")
            return
        
        export_format = self.comboBox_exportFormat.currentText()
        
        if len(self.current_layers) > 1:
            reply = QMessageBox.question(
                self,
                "Multiple Layers",
                f"You have {len(self.current_layers)} layers from your last download.\n\n"
                "Export all layers to separate files?\n\n"
                "Yes = All layers exported to a folder\n"
                "No = Choose one layer to export",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self._export_all_layers(export_format)
            elif reply == QMessageBox.No:
                self._choose_and_export_layer(export_format)
        else:
            self._export_single_layer(self.current_layers[0][1], export_format)

    def _choose_and_export_layer(self, export_format):
        """Let user choose which layer to export."""
        
        layer_names = [f"{cat.title()} ({layer.featureCount()} features)" 
                    for cat, layer in self.current_layers]
        
        selected_name, ok = QInputDialog.getItem(
            self,
            "Choose Layer to Export",
            "Select which layer to export:",
            layer_names,
            0, 
            False 
        )
        
        if ok and selected_name:
            selected_index = layer_names.index(selected_name)
            category, layer = self.current_layers[selected_index]
            
            self._export_single_layer(layer, export_format)
    
    def _export_single_layer(self, layer, export_format):
        """Export a single layer to file."""
        if export_format == "GeoJSON":
            filter_str = "GeoJSON Files (*.geojson);;All Files (*)"
            default_ext = ".geojson"
        elif export_format == "CSV":
            filter_str = "CSV Files (*.csv);;All Files (*)"
            default_ext = ".csv"
        else:
            QMessageBox.warning(self, "Invalid Format", "Please select a valid export format.")
            return
        
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
            success, error_msg = LayerExporter.export_to_geojson(layer, filepath)
        else:
            success, error_msg = LayerExporter.export_to_csv(layer, filepath)
        
        if success:
            feature_count = LayerExporter.get_feature_count(layer)
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
    
    def _export_all_layers(self, export_format):
        """Export all downloaded layers to separate files."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory for Export Files",
            ""
        )
        
        if not directory:
            return
        
        self.label_status.setText(f"Status: Exporting {len(self.current_layers)} layers...")
        self.pushButton_export.setEnabled(False)
        
        exported_count = 0
        failed_count = 0
        
        for category, layer in self.current_layers:
            safe_category = category.replace(" ", "_")
            filename = f"osm_{safe_category}.{export_format.lower()}"
            filepath = os.path.join(directory, filename)
            
            if export_format == "GeoJSON":
                success, error_msg = LayerExporter.export_to_geojson(layer, filepath)
            else:
                success, error_msg = LayerExporter.export_to_csv(layer, filepath)
            
            if success:
                exported_count += 1
            else:
                failed_count += 1
                print(f"Failed to export {category}: {error_msg}")
        
        if failed_count == 0:
            QMessageBox.information(
                self,
                "Export Successful",
                f"Exported all {exported_count} layers to:\n{directory}"
            )
            self.label_status.setText(f"Status: Exported {exported_count} layers")
        else:
            QMessageBox.warning(
                self,
                "Export Completed with Errors",
                f"Exported: {exported_count}\nFailed: {failed_count}\n\nCheck console for details."
            )
            self.label_status.setText(f"Status: Exported {exported_count}/{len(self.current_layers)} layers")
        
        self.pushButton_export.setEnabled(True)
    
    def export_map_with_legend(self):
        """Export the map canvas with automatic legend."""
        visible_layers = MapExporter.get_visible_layer_count()
        
        if visible_layers == 0:
            QMessageBox.warning(
                self,
                "No Layers",
                "No layers to export. Download POIs first."
            )
            return
        
        formats = ["PNG", "JPEG", "PDF"]
        format_choice, ok = QInputDialog.getItem(
            self,
            "Choose Export Format",
            "Select image format:",
            formats,
            0,
            False
        )
        
        if not ok:
            return
        
        title, ok = QInputDialog.getText(
            self,
            "Map Title",
            "Enter map title:",
            text="Risk Assessment Map"
        )
        
        if not ok:
            title = "Risk Assessment Map"
        
        if format_choice == "PNG":
            filter_str = "PNG Images (*.png)"
            default_ext = ".png"
        elif format_choice == "JPEG":
            filter_str = "JPEG Images (*.jpg *.jpeg)"
            default_ext = ".jpg"
        else:  
            filter_str = "PDF Documents (*.pdf)"
            default_ext = ".pdf"
        
        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Save Map",
            "",
            filter_str
        )
        
        if not filepath:
            return
        
        if not filepath.lower().endswith(default_ext):
            filepath += default_ext
        
        self.label_status.setText(f"Status: Exporting map to {format_choice}...")
        self.pushButton_exportMap.setEnabled(False)
        
        success, error_msg = MapExporter.export_map_with_legend(
            self.canvas,
            filepath,
            title,
            format_choice
        )
        
        if success:
            QMessageBox.information(
                self,
                "Export Successful",
                f"Map exported to:\n{filepath}\n\nThe map includes all visible layers and an automatic legend."
            )
            self.label_status.setText(f"Status: Map exported to {os.path.basename(filepath)}")
        else:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Could not export map:\n{error_msg}"
            )
            self.label_status.setText("Status: Map export failed")
        
        self.pushButton_exportMap.setEnabled(True)

        