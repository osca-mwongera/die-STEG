from qgis.core import QgsVectorLayer


def count_neighbours(layer: QgsVectorLayer) -> dict:
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
    return neighbour_count


if __name__ == '__console__':
    layer = QgsVectorLayer("/Buildings.shp", "Buildings", "ogr")
    if not layer.isValid():
        raise Exception('Layer is invalid')
    count_neighbours(layer=layer)