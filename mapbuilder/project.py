"""Project module contains Project class to define project properties to build custom maps.
"""
import os
import errno
import arcpy
import layer

def make_sure_path_exists(path):
    try:
        os.makedirs(path)
        print('\nPath did not exist previously.  Created: {}'.format(path))
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise


class Project(object):
    """Project class defines details needed for generating custom map outputs.
    """

    def __init__(self):
        """ Initialize variables. """
        self.name = 'Unnamed'
        self.author = 'Unknown'
        self.description = None
        self.base_path = None
        self.template_mxd = None    #'C:\\ArcGIS\\MXD Templates\\Base-FRCC-General-v4.mxd' # FIXME:  Move this to Config.py under ./templates
        self.workspace_path = None
        self.data_path = None
        self.style_path = None
        self.gdb_path = None
        self._mxd = None
        self.new_tables = list() # Holding place for tables before they are loaded
        self.new_layers = list() # Holding place for layers before they are loaded
        self._tables = list() # Tables added here after they have been loaded
        self._layers = list() # Layers added here after they have been loaded
        self.outputs = list() # Should be a list of output objects, including extents, visible layers, header/footer text, and output format.
        self.header_prefix = None
        self.output_prefix = None
        self.address_locator = None
        self.legend_x = 8.0703 # FIXME:  Set a default legend vaule that indicates NO LEGEND????
        self.legend_y = 0.5768


    def setPaths(self):
        self.workspace_path = os.path.join(self.base_path, 'Output')
        self.data_path = os.path.join(self.base_path, 'Data')
        self.style_path = os.path.join(self.base_path, 'Styles')

    def getMXDFile(self):
        """ Gets template MXD, triggers creation of new file, and returns
        ArcPy MapDocument object.
        """
        if self._mxd is None:
            mxd = self._startNewMXDFile()
            self._mxd = mxd
            self._InitProjectGDB()
        else:
            mxd = self._mxd
        return mxd


    def AddLayers(self):
        """

        :rtype: object
        """
        i = 0
        skipped = 0
        for x in xrange(0, len(self.new_layers)):
            layer = self.new_layers.pop()
 
            if layer.visible: # Don't bother adding if not visible
                self._addLayer(layer.path, layer.name, layer.definition_query)
                self._layers.append(layer)
                i += 1
            else:
                skipped += 1

        self._saveMXD()
        print ('\n%s new Layers added' % (i))
        print ('\n%s Layers skipped b/c of Visible status' % (skipped))


    def AddTables(self):
        i = 0
        for x in xrange(0, len(self.new_tables)):
            table = self.new_tables.pop()
            self._TableToTable(table.path, table.name)
            self._addTable(table.path)
            self._tables.append(table)
            i += 1
        print ('\n%s new Table(s) added' % (i))
        geocoded = self._GeocodeTables()
        print ('\n%s new Layer(s) Geocoded.' % (geocoded))
        self._saveMXD()

    def StyleLayers(self):
        for layer in self._layers:
            if layer.style:
                style_layer = arcpy.mapping.Layer(os.path.join(self.style_path, layer.style))
                self.ApplyStyle(layer.name, style_layer)

       
    def JoinTableToLayer(self, table_name, table_name_new, table_path,
                         layer_name, layer_path,
                         table_join_field = 'OBJECTID',
                         layer_join_field = 'OBJECTID'):
        """ Joins one table to a layer and appends it to the new_layers
        attribute of the instance."""

        # FIXME:  I can't find any usage of this method -- Make functional or remove

        
        table = os.path.join(table_path, table_name)

        arcpy.MakeFeatureLayer_management(layer_path, layer_name)
        arcpy.AddJoin_management(layer_name, layer_join_field,
                                 table, table_join_field)

        arcpy.FeatureClassToFeatureClass_conversion(layer_name, self.gdb_path,
                                                    table_name_new)

        new_path = os.path.join(self.gdb_path, table_name_new)
        return new_path
        #self.new_layers.append(layer.Layer(new_path, table_name_new))

    def JoinSpatialTableToLayer(self, definition):
        """ Uses Spatial join to find points within polygons.

        This module is likely more flexible than that, but that's what I
        have currently tested.
        """
        #print('In JoinSpatialTableToLayer.  definition: {}'.format(definition))
        layer_name = definition['layer_name']
        layer_path = definition['layer_path']
        table_name = definition['table_name']

        try:
            layer_style = definition['layer_style']
        except KeyError:
            layer_style = False

        out_name = layer_name + '__' + table_name
                                
        out_feature_class = self.gdb_path + '\\' + out_name
        join_features = self.gdb_path + '\\' + table_name
        
        arcpy.SpatialJoin_analysis(target_features=layer_path,
                                   join_features=join_features,
                                   out_feature_class=out_feature_class)

        new_layer = layer.Layer({'path': out_feature_class,
                                 'name': out_name,
                                 'style': layer_style,
                                 'definition_query': 'Join_Count > 0'
                                 })

        self.new_layers.append(new_layer)

    def AddCalculatedField(self, target_table_name, new_field_name, data_type, alias, calc):
        table_path = os.path.join(self.gdb_path, target_table_name)
        print ('\nAdding calculated field "%s" to table: %s' % (new_field_name, table_path))        
        arcpy.AddField_management(table_path, new_field_name, data_type, '', '', '', alias)
        arcpy.CalculateField_management(table_path, new_field_name, calc)


    def SortLayers(self, move_layer_name, ref_layer_name, insert_position):
        """ Sorts layers. """
        dataframe = self._getDataFrame()
        mxd = self.getMXDFile()

        move_layer = arcpy.mapping.ListLayers(mxd, move_layer_name, dataframe)[0]
        ref_layer = arcpy.mapping.ListLayers(mxd, ref_layer_name, dataframe)[0]

        arcpy.mapping.MoveLayer(dataframe, ref_layer, move_layer, insert_position)
        print ('\nMoved layer "%s" below layer "%s".' % (move_layer, ref_layer))


    def ApplyStyle(self, target_layer_name, style_layer_path):
        print('\nStyling layer %s.  Using layer as reference:  %s' % (target_layer_name, style_layer_path))
        dataframe = self._getDataFrame()
        mxd = self.getMXDFile()
        target_layer = arcpy.mapping.ListLayers(mxd, target_layer_name, dataframe)[0]
        arcpy.ApplySymbologyFromLayer_management(target_layer, style_layer_path)

    def LabelLayer(self, layer_name, label_expression):
        print('\nAddling labels to %s using expression %s' % (layer_name, label_expression))
        dataframe = self._getDataFrame()
        mxd = self.getMXDFile()
        target_layer = arcpy.mapping.ListLayers(mxd, layer_name, dataframe)[0]
        target_layer.labelClasses[0].expression = label_expression
        target_layer.showLabels = True
        arcpy.RefreshActiveView()

    def LegendStart(self):
        """ LegendStart enables legend auto add, so layers added after calling this
        method and before calling the LegendStop method will be included in the legend.
        """
        legend = arcpy.mapping.ListLayoutElements(self.getMXDFile(), "LEGEND_ELEMENT", "Legend")[0]
        legend.autoAdd = True
    

    def LegendStop(self):
        legend = arcpy.mapping.ListLayoutElements(self.getMXDFile(), "LEGEND_ELEMENT", "Legend")[0]
        legend.autoAdd = False

    def LegendPosition(self):
        legend = arcpy.mapping.ListLayoutElements(self.getMXDFile(), "LEGEND_ELEMENT", "Legend")[0]
        legend.elementPositionX = self.legend_x
        legend.elementPositionY = self.legend_y

    def LegendStyle(self, name = 'Horizontal with Heading and Labels'):
        legend = arcpy.mapping.ListLayoutElements(self.getMXDFile(),
                                                  "LEGEND_ELEMENT")[0]
        styleItem = arcpy.mapping.ListStyleItems("ESRI.style",
                                                 "Legend Items",
                                                 name)[0]
        for lyr in legend.listLegendItemLayers():
             legend.updateItem(lyr, styleItem)

 

    def SaveOutputs(self):
        mxd = self.getMXDFile()
        dataframe = self._getDataFrame()
        output_count = len(self.outputs)
        print ('\nSaving Output PDFs.  %s outputs found.' % (output_count))
        print ('Saving to project workspace:  %s' % (self.workspace_path))

        self._SetFooterText('(c) OpenStreet Map Contributers & U.S. Census Bureau')

        for output in self.outputs:
            if self.output_prefix:
                output_name = self.output_prefix + ' - ' + output['name']
            else:
                output_name = output['name']

            output_filename =  output_name + '.pdf'
            output_path =  os.path.join(self.workspace_path, output_filename)

            extent = dataframe.extent
            extent.XMin = output['xmin']
            extent.YMin = output['ymin']
            extent.XMax = output['xmax']
            extent.YMax = output['ymax']
            dataframe.extent = extent

            self._SetHeaderText(output['name'])
            arcpy.mapping.ExportToPDF(mxd, output_path)
            print('Saved:  %s' % (output_filename))
        self._saveMXD()


    def _GeocodeTables(self):
        i = 0
        for table in self._tables:
            print(table)
            if table.geocode:
                table_path = os.path.join(self.gdb_path, table.name)
                geocoded_name = table.geocoded_layer_name
                self._geocode(table_path, geocoded_name)
                geocoded_layer_path = os.path.join(self.gdb_path, geocoded_name)
                geocoded_layer = layer.Layer({'path': geocoded_layer_path,
                                              'name': geocoded_name,
                                              'style': table.geocode_layer_style,
                                              'visible': table.visible})

                self.new_layers.append(geocoded_layer)
                i += 1
        return i

    def _geocode(self, table, out_name):
        address_locator = self.address_locator
        address_fields = "Street street_1; City city; State state; Zip zip"
        out_feature_class = os.path.join(self.gdb_path, out_name)
        msg = '\nGeocoding table:  %s\nOutput name: %s\nOutput Path: %s\nLocator: %s\nAddress Fields: %s'
        msg = msg % (table, out_name, out_feature_class, address_locator, address_fields)
        print(msg)
        arcpy.GeocodeAddresses_geocoding(table,
                                         address_locator,
                                         address_fields,
                                         out_feature_class)
                                         

 
    def _SetHeaderText(self, line2_text):
        print ('\nUpdating header for %s.' % (line2_text))
        for txt in arcpy.mapping.ListLayoutElements(self.getMXDFile(), "TEXT_ELEMENT"):
            if txt.name == 'txtHeader':
                txt.text = '<FNT size="18"><BOL>Front Range Community College</BOL></FNT>'
                txt.text += '\r\n<FNT size="14"><BOL>%s</BOL></FNT>' % (self.header_prefix)
                txt.text += '\r\n<FNT size="14">%s</FNT>' % (line2_text)
    
    def _SetFooterText(self, copyright_text):
        print ('\nUpdating footer text fields.')
        for txt in arcpy.mapping.ListLayoutElements(self.getMXDFile(), "TEXT_ELEMENT"):
            if txt.name == 'txtLowerLeft':
                txt.text = copyright_text
            elif txt.name == 'txtLowerRight':
                txt.text = 'Generated:  <dyn format="short" type="date">'

    
    def _InitProjectGDB(self):
        """ Sets up the GDB for the project to use for storing data in. """
        name = self.name + '.gdb'
        self.gdb_path = os.path.join(self.workspace_path, name)
        print('\nCreating project GDB at: %s' % (self.gdb_path))
        if arcpy.Exists(self.gdb_path):
            arcpy.Delete_management(self.gdb_path)
        arcpy.CreateFileGDB_management(self.workspace_path, name)        


    def _TableToTable(self, path, table_name):
        """ Loads data table to the project's GDB for use in a project."""
        in_rows = path
        out_path = self.gdb_path
        out_name = table_name
        
        if arcpy.Exists(out_path + '\\' + out_name):
            print('removing existing table:  {}'.format(out_path + '\\' + out_name))
            arcpy.Delete_management(out_path + '\\' + out_name)

        print('\nLoading from {} to {}.  Target name: {}'.format(in_rows, out_path, out_name))
        arcpy.TableToTable_conversion(in_rows, out_path, out_name)


    def _addTable(self, path):
        """ Adds a data table to the project's MXD file from the specified path."""

        dataframe = self._getDataFrame()
        table = arcpy.mapping.TableView(path)
        print('\nLoading table:  %s' % (table.name))
        arcpy.mapping.AddTableView(dataframe, table)


    def _addLayer(self, path, name, definition_query=''):
        """ Adds a layer to the project's MXD file from the specified path.

        A common usage of this is to add a Feature Class from a GDB.
        """
        dataframe = self._getDataFrame()
        print('\nLoading Layer (%s) from path: %s' % (name, path))
        layer = arcpy.mapping.Layer(path)
        layer.definitionQuery = definition_query
        arcpy.mapping.AddLayer(dataframe, layer)
        

    def _startNewMXDFile(self):
        """ Uses the project's name to save a new copy of the Template MXD file.

        Requires an ArcPy MapDocument object.
        """
        print('\nUsing initial mxd Template: %s' % ( self.template_mxd))
        path = os.path.join(self.workspace_path, self.name + '.mxd')

        make_sure_path_exists(self.workspace_path)
        
        mxd = arcpy.mapping.MapDocument(self.template_mxd)
        mxd.title = self.name
        mxd.author = self.author
        print('\nSaving to Path:  %s' % (path))
        mxd.saveACopy(path)
        return arcpy.mapping.MapDocument(path)

    def _getDataFrame(self):
        """ Uses MXD file object to return data frame."""
        mxd = self.getMXDFile()
        dataframe = arcpy.mapping.ListDataFrames(mxd,"*")[0]
        return dataframe

    def _saveMXD(self):
        mxd = self.getMXDFile()
        mxd.save()
        
