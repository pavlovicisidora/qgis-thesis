# -*- coding: utf-8 -*-
"""
Module for exporting QGIS layers to various formats.
"""
from qgis.core import QgsVectorFileWriter, QgsCoordinateTransformContext
import os


class LayerExporter:
    """
    Handles exporting QGIS vector layers to different file formats.
    """
    
    @staticmethod
    def export_to_geojson(layer, filepath):
        """
        Export a QGIS vector layer to GeoJSON format.
        
        Args:
            layer: QgsVectorLayer to export
            filepath: String, full path where file should be saved (including .geojson extension)
        
        Returns:
            Tuple (success: bool, error_message: str or None)
        """
        if not layer or not layer.isValid():
            return False, "Invalid layer"
        
        if not filepath.lower().endswith('.geojson'):
            filepath += '.geojson'
        
        save_options = QgsVectorFileWriter.SaveVectorOptions()
        save_options.driverName = "GeoJSON"
        save_options.fileEncoding = "UTF-8"
        
        error = QgsVectorFileWriter.writeAsVectorFormatV3(
            layer,
            filepath,
            QgsCoordinateTransformContext(),
            save_options
        )
        
        if error[0] == QgsVectorFileWriter.NoError:
            return True, None
        else:
            return False, f"Export failed: {error[1]}"
    
    @staticmethod
    def export_to_csv(layer, filepath):
        """
        Export a QGIS vector layer to CSV format (coordinates + attributes).
        
        Args:
            layer: QgsVectorLayer to export
            filepath: String, full path where file should be saved (including .csv extension)
        
        Returns:
            Tuple (success: bool, error_message: str or None)
        """
        if not layer or not layer.isValid():
            return False, "Invalid layer"
        
        if not filepath.lower().endswith('.csv'):
            filepath += '.csv'
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                fields = [field.name() for field in layer.fields()]
                header = ['longitude', 'latitude'] + fields
                f.write(','.join(header) + '\n')
                
                for feature in layer.getFeatures():
                    geom = feature.geometry()
                    if geom and not geom.isEmpty():
                        point = geom.asPoint()
                        lon = point.x()
                        lat = point.y()
                        
                        attributes = [str(feature[field]) for field in fields]
                        
                        row = [str(lon), str(lat)] + attributes
                        f.write(','.join(row) + '\n')
            
            return True, None
            
        except Exception as e:
            return False, f"CSV export failed: {str(e)}"
    
    @staticmethod
    def get_feature_count(layer):
        """
        Get the number of features in a layer.
        
        Args:
            layer: QgsVectorLayer
        
        Returns:
            Integer count, or 0 if layer is invalid
        """
        if layer and layer.isValid():
            return layer.featureCount()
        return 0
