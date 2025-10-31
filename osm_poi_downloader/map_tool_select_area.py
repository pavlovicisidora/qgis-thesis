# -*- coding: utf-8 -*-
"""
Map tool for selecting a rectangular area on the map canvas.
"""
from qgis.PyQt.QtCore import Qt, pyqtSignal
from qgis.PyQt.QtGui import QColor
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.core import QgsWkbTypes, QgsRectangle, QgsPointXY


class MapToolSelectArea(QgsMapTool):
    """
    Map tool that allows user to draw a rectangle on the map.
    Emits a signal with the bounding box when selection is complete.
    """
    areaSelected = pyqtSignal(QgsRectangle)
    
    def __init__(self, canvas):
        """
        Constructor.
        
        Args:
            canvas: QgsMapCanvas instance
        """
        super(MapToolSelectArea, self).__init__(canvas)
        self.canvas = canvas
        self.rubberBand = None
        self.startPoint = None
        self.endPoint = None
        self.isDrawing = False
        
        self.setCursor(Qt.CrossCursor)
        
    def canvasPressEvent(self, event):
        """
        Handle mouse press - start drawing rectangle.
        """
        if event.button() == Qt.LeftButton:
            self.startPoint = self.toMapCoordinates(event.pos())
            self.endPoint = self.startPoint
            self.isDrawing = True
            
            if self.rubberBand is None:
                self.rubberBand = QgsRubberBand(self.canvas, QgsWkbTypes.PolygonGeometry)
                self.rubberBand.setColor(QColor(255, 0, 0, 50))
                self.rubberBand.setWidth(2)
                
            self.showRect(self.startPoint, self.endPoint)
            
    def canvasMoveEvent(self, event):
        """
        Handle mouse move - update rectangle while dragging.
        """
        if self.isDrawing:
            self.endPoint = self.toMapCoordinates(event.pos())
            self.showRect(self.startPoint, self.endPoint)
            
    def canvasReleaseEvent(self, event):
        """
        Handle mouse release - finalize rectangle selection.
        """
        if event.button() == Qt.LeftButton and self.isDrawing:
            self.endPoint = self.toMapCoordinates(event.pos())
            self.isDrawing = False
            
            rect = QgsRectangle(self.startPoint, self.endPoint)
            
            self.areaSelected.emit(rect)
            
            if self.rubberBand:
                self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)
                
    def showRect(self, startPoint, endPoint):
        """
        Update the rubber band to show current rectagnle.
        """
        if self.rubberBand and startPoint and endPoint:
            self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)
            rect = QgsRectangle(startPoint, endPoint)
            
            points = [
                QgsPointXY(rect.xMinimum(), rect.yMinimum()),
                QgsPointXY(rect.xMaximum(), rect.yMinimum()),
                QgsPointXY(rect.xMaximum(), rect.yMaximum()),
                QgsPointXY(rect.xMinimum(), rect.yMaximum())
            ]
            
            for point in points:
                self.rubberBand.addPoint(point, False)
            self.rubberBand.addPoint(points[0], True)  # Close the polygon
            self.rubberBand.show()
            
    def deactivate(self):
        """
        Clean up when tool is deactivated.
        """
        if self.rubberBand:
            self.rubberBand.reset(QgsWkbTypes.PolygonGeometry)
        super(MapToolSelectArea, self).deactivate()
    