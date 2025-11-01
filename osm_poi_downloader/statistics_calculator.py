# -*- coding: utf-8 -*-
"""
Module for calculating statistics about downloaded POI data.
"""
from qgis.core import QgsDistanceArea, QgsCoordinateReferenceSystem
import math


class StatisticsCalculator:
    """
    Calculates statistics about POI layers and bounding boxes.
    """
    
    @staticmethod
    def calculate_bbox_area(bbox):
        """
        Calculate the area of a bounding box in square kilometers.
        
        Args:
            bbox: Tuple of (south, west, north, east) in WGS84 coordinates
        
        Returns:
            Float, area in square kilometers
        """
        south, west, north, east = bbox
        
        mid_lat = (south + north) / 2
        
        lat_to_km = 111.32 
        lon_to_km = 111.32 * math.cos(math.radians(mid_lat)) 
        
        height_km = (north - south) * lat_to_km
        width_km = (east - west) * lon_to_km
        
        area_km2 = height_km * width_km
        
        return area_km2
    
    @staticmethod
    def calculate_density(feature_count, area_km2):
        """
        Calculate POI density.
        
        Args:
            feature_count: Integer, number of POIs
            area_km2: Float, area in square kilometers
        
        Returns:
            Float, POIs per square kilometer
        """
        if area_km2 == 0:
            return 0
        return feature_count / area_km2
    
    @staticmethod
    def format_statistics(feature_count, bbox, category):
        """
        Generate a formatted statistics string for display.
        
        Args:
            feature_count: Integer, number of POIs downloaded
            bbox: Tuple of (south, west, north, east) in WGS84
            category: String, POI category name
        
        Returns:
            String with formatted statistics
        """
        south, west, north, east = bbox
        
        area_km2 = StatisticsCalculator.calculate_bbox_area(bbox)
        
        density = StatisticsCalculator.calculate_density(feature_count, area_km2)
        
        stats = f"""<b>POIs Found:</b> {feature_count} {category}(s)<br>
                    <br>
                    <b>Area Covered:</b> {area_km2:.3f} km²<br>
                    <br>
                    <b>Density:</b> {density:.2f} POIs/km²<br>
                    <br>
                    <b>Bounding Box:</b><br>
                    &nbsp;&nbsp;South: {south:.4f}°<br>
                    &nbsp;&nbsp;West: {west:.4f}°<br>
                    &nbsp;&nbsp;North: {north:.4f}°<br>
                    &nbsp;&nbsp;East: {east:.4f}°"""
        
        return stats
    
    @staticmethod
    def get_layer_bounds(layer):
        """
        Get the geographic bounds of a layer.
        
        Args:
            layer: QgsVectorLayer
        
        Returns:
            Tuple of (south, west, north, east) or None if layer is invalid
        """
        if not layer or not layer.isValid():
            return None
        
        extent = layer.extent()
        
        west = extent.xMinimum()
        east = extent.xMaximum()
        south = extent.yMinimum()
        north = extent.yMaximum()
        
        return (south, west, north, east)
    