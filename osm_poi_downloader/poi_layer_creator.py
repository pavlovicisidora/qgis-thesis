# -*- coding: utf-8 -*-
"""
Module for creating QGIS layers from POI data.
"""
from qgis.core import (
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsField,
    QgsProject,
    QgsMarkerSymbol
)
from qgis.PyQt.QtCore import QVariant, QMetaType


class PoiLayerCreator:
    """
    Creates QGIS vector layers from POI data.
    """
    
    CATEGORY_COLORS = {
        'restaurant': '#e74c3c',
        'cafe': '#f39c12',
        'hospital': '#3498db',
        'school': '#9b59b6',
        'bank': '#2ecc71',
        'atm': '#1abc9c',
        'pharmacy': '#e67e22',
        'gas station': '#34495e',
        'supermarket': '#27ae60',
        'mall': '#8e44ad',
        'bus station': '#c0392b',
        'train station': '#2c3e50',
        'hotel': '#16a085',
    }
    
    @staticmethod
    def create_layer(features, layer_name, poi_type):
        """
        Create a QGIS point layer from POI features.
        """
        if not features:
            print("ERROR: No features to create layer from")
            return None
        
        print(f"Creating layer with {len(features)} features")
        
        layer = QgsVectorLayer('Point?crs=EPSG:4326', layer_name, 'memory')
        
        if not layer.isValid():
            print("ERROR: Could not create layer")
            return None
            
        provider = layer.dataProvider()
        
        fields = [
            QgsField('id', QMetaType.Type.LongLong),
            QgsField('name', QMetaType.Type.QString),
            QgsField('type', QMetaType.Type.QString),
            QgsField('address', QMetaType.Type.QString),
            QgsField('phone', QMetaType.Type.QString),
            QgsField('website', QMetaType.Type.QString),
            QgsField('opening_hours', QMetaType.Type.QString),
        ]
        
        provider.addAttributes(fields)
        layer.updateFields()
        
        print(f"Layer fields: {[f.name() for f in layer.fields()]}")
        
        qgs_features = []
        for i, feat in enumerate(features):
            qgs_feat = QgsFeature(layer.fields())
            
            lon = feat.get('lon')
            lat = feat.get('lat')
            
            if lon is None or lat is None:
                print(f"WARNING: Feature {i} has no coordinates, skipping")
                continue
                
            point = QgsPointXY(lon, lat)
            qgs_feat.setGeometry(QgsGeometry.fromPointXY(point))
            
            tags = feat.get('tags', {})
            qgs_feat.setAttribute('id', int(feat.get('id', 0)))
            qgs_feat.setAttribute('name', str(feat.get('name', 'Unnamed')))
            qgs_feat.setAttribute('type', str(feat.get('type', 'unknown')))
            qgs_feat.setAttribute('address', str(tags.get('addr:full', tags.get('addr:street', ''))))
            qgs_feat.setAttribute('phone', str(tags.get('phone', tags.get('contact:phone', ''))))
            qgs_feat.setAttribute('website', str(tags.get('website', tags.get('contact:website', ''))))
            qgs_feat.setAttribute('opening_hours', str(tags.get('opening_hours', '')))
            
            qgs_features.append(qgs_feat)
        
        print(f"Adding {len(qgs_features)} features to layer")
        
        result = provider.addFeatures(qgs_features)
        
        if result[0]: 
            print(f"SUCCESS: Added {len(result[1])} features")
        else:
            print("ERROR: Failed to add features to layer")
            return None
            
        layer.updateExtents()
        
        print(f"Layer extent: {layer.extent().toString()}")
        print(f"Layer feature count: {layer.featureCount()}")
        
        PoiLayerCreator.style_layer(layer, poi_type)
        
        return layer
    
    @staticmethod
    def style_layer(layer, poi_type):
        """
        Apply styling to the POI layer.
        """
        color = PoiLayerCreator.CATEGORY_COLORS.get(poi_type.lower(), '#95a5a6')
        
        symbol = QgsMarkerSymbol.createSimple({
            'name': 'circle',
            'color': color,
            'size': '4',
            'outline_color': 'black',
            'outline_width': '0.8'
        })
        
        layer.renderer().setSymbol(symbol)
        layer.triggerRepaint()
    
    @staticmethod
    def add_layer_to_project(layer):
        """
        Add the layer to the current QGIS project.
        """
        if not layer:
            print("ERROR: No layer to add")
            return False
            
        if not layer.isValid():
            print("ERROR: Cannot add invalid layer to project")
            return False
        
        QgsProject.instance().addMapLayer(layer)
        print(f"Layer '{layer.name()}' added to project with {layer.featureCount()} features")
        return True
    