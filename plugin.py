import os
from qgis.core import QgsVectorLayer, QgsProject, QgsFeature, QgsField, QgsPrintLayout, QgsLayoutItemPage, QgsLayoutItemMap, \
     QgsLayoutPoint, QgsUnitTypes, QgsLayoutSize, QgsLayoutMeasurement, QgsLayoutItemLabel, QgsLayoutItemScaleBar, \
     QgsLayoutItemLegend, QgsLayoutItemPicture
from qgis.PyQt.QtCore import QVariant, Qt
from qgis.PyQt.QtGui import QColor, QFont
from qgis.utils import iface


class NeighboursLayer:
    """
    This class takes in a polygon (Building) layer, colours all buildings with a red dot if they have more than one neighbour.
    """
    def __init__(self, layer):
        self.layer : QgsVectorLayer = layer
    
    def get_features_with_more_than_a_neighbour(self) -> dict:
        """
        Counts neighbours to a polygon feature and returns their indices in the layer as keys in a dictionary with the count of neighbours as the value
        """

        # Initialize neighbour count dictionary
        neighbour_count = {}

        features = self.layer.getFeatures()

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

    def symbolize_layer(self) -> None:
        neighbours: dict = self.get_features_with_more_than_a_neighbour()
        point_layer = QgsVectorLayer("Point?crs=EPSG:4326", "My Points", "memory") # Create Layer to hold the point features in memory
        point_layer.setCrs(self.layer.crs()) # Reset the layer projection to match the buildings layer
        point_provider = point_layer.dataProvider()
        point_provider.addAttributes([QgsField("neighbours", QVariant.Int)]) # Add neighbour attribute to be populated with the building's number of neighbours
        point_layer.updateFields()
        
        for key, value in neighbours.items():
            centroid_geometry = self.layer.getFeature(fid=key).geometry().centroid() # get the geometry of the feature centroid
            feature = QgsFeature()
            feature.setAttributes([value]) # add neighbour attribute
            feature.setGeometry(geometry=centroid_geometry)
            point_provider.addFeature(feature=feature) # Add the point feature to the point layer
        point_layer.updateExtents()

        # Add layer to map and visualize it with a red colour and an appropriate shade
        QgsProject.instance().addMapLayer(point_layer)
        symbol  = point_layer.renderer().symbol()
        symbol.setColor(QColor("red"))
        symbol.setSize(3)
        point_layer.triggerRepaint()

        return None

def create_layout(layout_name: str):
    project = QgsProject.instance()
    existing_layout = project.layoutManager().layoutByName(name=layout_name)  # Returns the layout with a matching name, or None if no matching layouts were found.

    if existing_layout is not None:
        project.layoutManager().removeLayout(layout=existing_layout)
    
    layout = QgsPrintLayout(project=project) # Create a new layout and set it properties
    layout.initializeDefaults() # Set layout size (A4 in mm)
    layout.setName(layout_name)
    
    pc = layout.pageCollection()
    pc.page(0).setPageSize('A4', QgsLayoutItemPage.Orientation.Landscape) # Turn layout canvas to Landscape mode

    project.layoutManager().addLayout(layout)
    return layout

def add_map_item(layout: QgsPrintLayout) -> None:
    map = QgsLayoutItemMap(layout)
    # Set map item position and size (by default, it is a 0 width/0 height item placed at 0,0)
    map.attemptMove(QgsLayoutPoint(22,24, QgsUnitTypes.LayoutMillimeters))
    map.attemptResize(QgsLayoutSize(222,153, QgsUnitTypes.LayoutMillimeters))
    # Provide an extent to render
    map.zoomToExtent(iface.mapCanvas().extent())

    # Add map frame
    map.setFrameEnabled(drawFrame=True)
    map.setFrameStrokeColor(color=QColor("black"))
    map.setFrameStrokeWidth(width=QgsLayoutMeasurement(length=0.30, units=QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(map)
    return map

def add_map_title(layout: QgsPrintLayout) -> None:
    title = QgsLayoutItemLabel(layout=layout)
    title.setText(text="A Map of Buildings with more than one Neighbour in Feuerbach, Stuttgart")
    
    title_font = QFont("Helvetica", pointSize=16, weight=6, italic=False)
    title_font.setBold(True)
    title_font.setUnderline(True)
    title.setFont(font=title_font)
    title.setFontColor(color=QColor("black"))

    title.attemptMove(QgsLayoutPoint(35,7, QgsUnitTypes.LayoutMillimeters))
    title.attemptResize(QgsLayoutSize(205,11, QgsUnitTypes.LayoutMillimeters))
    title.setHAlign(alignment=Qt.AlignmentFlag.AlignHCenter)
    title.setVAlign(alignment=Qt.AlignmentFlag.AlignVCenter)
    layout.addLayoutItem(title)
    return None

def add_scale_bar(layout: QgsPrintLayout) -> None:
    scale = QgsLayoutItemScaleBar(layout=layout)
    scale.applyDefaultSettings()
    scale.setUnits(units=QgsUnitTypes.DistanceMeters)
    scale.setUnitLabel(label="m")

    scale.setLinkedMap(map=add_map_item(layout=layout))

    scale.attemptMove(QgsLayoutPoint(62,181, QgsUnitTypes.LayoutMillimeters))
    scale.setUnitsPerSegment(100)
    scale.setMapUnitsPerScaleBarUnit(1)
    layout.addLayoutItem(scale)
    return None

def add_legend(layout: QgsPrintLayout) -> None:
    
    legend = QgsLayoutItemLegend(layout=layout)
    legend.setLinkedMap(map=add_map_item(layout=layout))
    legend.setTitle(title="Legend")
    legend.setTitleAlignment(alignment=Qt.AlignmentFlag.AlignCenter)
    legend.attemptMove(QgsLayoutPoint(249,130, QgsUnitTypes.LayoutMillimeters))
    legend.resizeToContents()
    layout.addLayoutItem(legend)
    return None

def add_north_arrow(layout: QgsPrintLayout, arrow_path) -> None:
    north_arrow = QgsLayoutItemPicture(layout=layout)
    north_arrow.setNorthMode(QgsLayoutItemPicture.NorthMode.GridNorth)
    north_arrow.setMode(QgsLayoutItemPicture.Format.FormatSVG)
    north_arrow.setResizeMode(QgsLayoutItemPicture.ResizeMode.Zoom)
    north_arrow.setLinkedMap(map=add_map_item(layout=layout))
    north_arrow.setPicturePath(path=arrow_path)
    
    north_arrow.attemptMove(QgsLayoutPoint(249,23, QgsUnitTypes.LayoutMillimeters))
    north_arrow.attemptResize(QgsLayoutSize(width=48, height=88, units=QgsUnitTypes.LayoutMillimeters))
    layout.addLayoutItem(north_arrow)
    return None

if __name__ == '__console__':
    qgs_project_path = QgsProject.instance().readPath("./")
    # layer_relative_path = "/Output/Buildings.shp"
    # layer_path = qgs_project_path + layer_relative_path
    # layer = QgsVectorLayer(layer_path, "Buildings", "ogr")
    # if not layer.isValid():
    #     raise Exception('Layer is invalid')
    # NeighboursLayer(layer=layer).symbolize_layer()

    layout = create_layout(layout_name="Buildings of Feuerbach with more than one neighbour")

    # add_map_item(layout=layout)
    # add_map_title(layout=layout)
    add_legend(layout=layout)
    arrow_path = qgs_project_path + "/Input/NorthArrow_04.svg"
    add_north_arrow(layout=layout, arrow_path=arrow_path)

