# -*- coding: utf-8 -*-
"""
Module for exporting map canvas with automatic legend.
"""
from qgis.core import (
    QgsProject,
    QgsLayoutExporter,
    QgsLayout,
    QgsLayoutItemMap,
    QgsLayoutItemLegend,
    QgsLayoutItemLabel,
    QgsLayoutItemPage,
    QgsLayoutItemScaleBar,
    QgsLayoutPoint,
    QgsLayoutSize,
    QgsUnitTypes,
    QgsLegendStyle,
    QgsTextFormat
)
from qgis.PyQt.QtCore import QRectF, QSizeF
from qgis.PyQt.QtGui import QFont, QColor
import os


class MapExporter:
    
    @staticmethod
    def export_map_with_legend(canvas, filepath, title="Risk Assessment Map", format="PNG"):
        """
        Export the current map canvas with an automatic legend.
        
        Args:
            canvas: QgsMapCanvas instance
            filepath: String, full path where file should be saved
            title: String, map title to display
            format: String, export format ("PNG", "JPEG", or "PDF")
        
        Returns:
            Tuple (success: bool, error_message: str or None)
        """
        try:
            project = QgsProject.instance()
            layout = QgsLayout(project)
            layout.initializeDefaults()
            
            page_collection = layout.pageCollection()
            page = page_collection.page(0)
            page.setPageSize('A4', QgsLayoutItemPage.Landscape)
            
            page_width = page.pageSize().width()
            page_height = page.pageSize().height()
            
            title_item = QgsLayoutItemLabel(layout)
            title_item.setText(title)
            title_font = QFont('Arial', 16, QFont.Bold)
            title_item.setFont(title_font)
            title_item.attemptResize(QgsLayoutSize(page_width - 20, 15))
            title_item.attemptMove(QgsLayoutPoint(10, 5))
            layout.addLayoutItem(title_item)
            
            map_item = QgsLayoutItemMap(layout)
            map_item.attemptResize(QgsLayoutSize(page_width * 0.65, page_height - 30))
            map_item.attemptMove(QgsLayoutPoint(10, 25))
            
            map_item.setExtent(canvas.extent())
            map_item.setCrs(canvas.mapSettings().destinationCrs())
            
            layout.addLayoutItem(map_item)
            
            legend = QgsLayoutItemLegend(layout)
            legend.setTitle("Legend")
            
            legend.setAutoUpdateModel(True)
            legend.setLinkedMap(map_item)
            
            root = QgsProject.instance().layerTreeRoot()
            legend_model = legend.model()
            legend_model.setRootGroup(root)
            
            MapExporter._filter_legend_layers(legend)
            
            legend_width = page_width * 0.25
            legend_height = page_height - 30
            legend.attemptResize(QgsLayoutSize(legend_width, legend_height))
            legend.attemptMove(QgsLayoutPoint(page_width - legend_width - 5, 25))
            
            title_format = QgsTextFormat()
            title_format.setFont(QFont('Arial', 12, QFont.Bold))
            title_format.setColor(QColor(0, 0, 0))
            legend.setStyleFont(QgsLegendStyle.Title, title_format.font())
            
            group_format = QgsTextFormat()
            group_format.setFont(QFont('Arial', 10, QFont.Bold))
            legend.setStyleFont(QgsLegendStyle.Group, group_format.font())
            
            subgroup_format = QgsTextFormat()
            subgroup_format.setFont(QFont('Arial', 9))
            legend.setStyleFont(QgsLegendStyle.Subgroup, subgroup_format.font())
            
            layout.addLayoutItem(legend)
            
            exporter = QgsLayoutExporter(layout)
            
            if format.upper() == "PNG":
                export_settings = QgsLayoutExporter.ImageExportSettings()
                export_settings.dpi = 300
                result = exporter.exportToImage(filepath, export_settings)
                
            elif format.upper() == "JPEG":
                export_settings = QgsLayoutExporter.ImageExportSettings()
                export_settings.dpi = 300
                result = exporter.exportToImage(filepath, export_settings)
                
            elif format.upper() == "PDF":
                export_settings = QgsLayoutExporter.PdfExportSettings()
                export_settings.dpi = 300
                result = exporter.exportToPdf(filepath, export_settings)
            else:
                return False, f"Unsupported format: {format}"
            
            if result == QgsLayoutExporter.Success:
                return True, None
            else:
                return False, f"Export failed with code: {result}"
                
        except Exception as e:
            return False, f"Export error: {str(e)}"
    
    @staticmethod
    def _filter_legend_layers(legend):
        """
        Filter legend to only show visible layers with features.
        
        Args:
            legend: QgsLayoutItemLegend instance
        """
        try:
            model = legend.model()
            root = model.rootGroup()
            
            for layer_node in root.children():
                if hasattr(layer_node, 'layer'):
                    layer = layer_node.layer()
                    if layer and hasattr(layer, 'featureCount'):
                        if layer.featureCount() == 0:
                            model.setLayerTreeNodeData(layer_node, 'checked', False)
        except Exception as e:
            print(f"Warning: Could not filter legend layers: {e}")
    
    @staticmethod
    def get_visible_layer_count():
        """
        Get count of visible vector layers in the project.
        
        Returns:
            Integer count of visible layers
        """
        count = 0
        for layer in QgsProject.instance().mapLayers().values():
            if hasattr(layer, 'featureCount') and layer.featureCount() > 0:
                count += 1
        return count
    