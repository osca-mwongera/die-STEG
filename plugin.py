from qgis.core import QgsVectorLayer, QgsProject, QgsFeature, QgsField
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.QtGui import QColor

def get_features_with_more_than_a_neighbour(layer: QgsVectorLayer) -> dict:
    # Initialize neighbour count dictionary
    neighbour_count = {}

    features = layer.getFeatures()

    # Iterate over each polygon feature
    for feature in features:
        f_id = feature.id()
        geom = feature.geometry()
        neighbour_count[f_id] = 0
        
        # Check against all other polygon features
        for other_feature in layer.getFeatures():
            if f_id != other_feature.id() and geom.touches(other_feature.geometry()):  # Avoid comparing to self
                neighbour_count[f_id] += 1
    for k in list(neighbour_count.keys()): # delete feature ids with neighbours less than one or equal to one
        if neighbour_count[k] <= 1:
            del neighbour_count[k]
    return neighbour_count

def symbolize_layer(layer: QgsVectorLayer, neighbours: dict) -> None:
    point_layer = QgsVectorLayer("Point?crs=EPSG:4326", "My Points", "memory") # Create Layer to hold the point features in memory
    point_layer.setCrs(layer.crs()) # Reset the layer projection to match the buildings layer
    point_provider = point_layer.dataProvider()
    point_provider.addAttributes([QgsField("neighbours", QVariant.Int)]) # Add neighbour attribute to be populated with the building's number of neighbours
    point_layer.updateFields()
    
    for key, value in neighbours.items():
        centroid_geometry = layer.getFeature(fid=key).geometry().centroid() # get the geometry of the feature centroid
        feature = QgsFeature()
        feature.setAttributes([value]) # add neighbour attribute
        feature.setGeometry(geometry=centroid_geometry)
        point_provider.addFeature(feature=feature) # Add the point feature to the point layer
    point_layer.updateExtents()

    # Add layer to map and visualize it with a red colour and an appropriate shade
    QgsProject.instance().addMapLayer(point_layer)
    symbol  = point_layer.renderer().symbol()
    symbol.setColor(QColor("red"))
    symbol.setSize(5)
    point_layer.triggerRepaint()



    return None


if __name__ == '__console__':
    layer = QgsVectorLayer("Buildings.shp", "Buildings 1", "ogr")
    if not layer.isValid():
        raise Exception('Layer is invalid')
    symbolize_layer(layer=layer, neighbours=get_features_with_more_than_a_neighbour(layer=layer))