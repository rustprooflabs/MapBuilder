"""This Module will soon become much simpler.  It's been my scratch pad
during development and probably contains way too many things in it.  
"""
import arcpy
import os

from mapbuilder import project, layer, table, config

__version__ = '0.4.7'

class Controller:
    """ The controller class provides the basic logic for automating ArcGIS projects."""
    def __init__(self):
        self.config = config.Config()

            
    def run(self):
        """ Processes a project based on the configuration object defined during
        instantiation.
        """
        self._inititeProject()

        self._addTablesToProject() # This step adds any geocoded tables to layers
        self._runSpatialJoins() # These are also added to layers.
        self._addLayersToProject() # Needs to run after adding tables and spatial joins

        self._sort_layers()

        # Setup Legend
        self.prj.LegendStart()

        self.prj.LegendPosition()
        self.prj.LegendStyle()
        self.prj.LegendStop()

        self.prj.StyleLayers()

        self._save_outputs()


    def _inititeProject(self):
        """ Initiates project based on defined Config class. """
        self.prj = project.Project()

        # Set Generic Project Details
        self.prj.name = self.config.PROJECT_NAME
        self.prj.author = self.config.PROJECT_AUTHOR
        self.prj.base_path = self.config.PROJECT_BASE_PATH
        self.prj.setPaths()
        self.prj.description = self.config.PROJECT_DESCRIPTION

        # Set MXD Template to use
        self.prj.template_mxd = self.config.TEMPLATE_MXD

        # Set dynamic text elements
        self.prj.header_prefix = self.config.OUTPUT_HEADER_PREFIX
        self.prj.output_prefix = self.config.OUTPUT_FILE_PREFIX

        # Set Legend position for Output (PDF)
        self.prj.legend_x = self.config.LEGEND_X
        self.prj.legend_y = self.config.LEGEND_Y

        self.prj.address_locator = self.config.ADDRESS_LOCATOR

        # I'm not sure this is needed, should try testing at some point in the future...
        arcpy.env.overwriteOutput = True

        # Called to ensure new MXDFile is created, even if layers/tables aren't added.
        self.prj.getMXDFile()

    
    def _addTablesToProject(self):
        """ Prepares defined data (attribute) table(s) to project.
        
        This method takes data from project's config and creates Table objects using the Table class.

        Other than appending the items to the list this handles differences between normal data files
        (e.g. Tab delimited .txt file) vs Attribute tables already stored in a GDB.
        """
        prj = self.prj
        for tbl in self.config.TABLES:
            # If extension set, it's a data source like ".txt", otherwise it's assumed to be in a DBF.
            if tbl['extension']:
                data_name = tbl['name'] + tbl['extension']
            else:
                data_name = tbl['name']

            # Uses defined path if provided, otherwise uses project's default data path.
            if tbl['path']:
                data_path = os.path.join(tbl['path'], data_name)
            else:
                data_path = os.path.join(prj.data_path, data_name)

            tbl['path'] = data_path
            tbl = table.Table(tbl)
            prj.new_tables.append(tbl)

        prj.AddTables()

    def _addLayersToProject(self):
        """ Adds definitions of existing spatial layer(s) to the project.
        
        This method takes data from project's config and creates Layer objects using the Layer class.
        """
        prj = self.prj
        for lyr in self.config.LAYERS:
            lyr = layer.Layer(lyr)
            prj.new_layers.append(lyr)

        prj.AddLayers()

    def _runSpatialJoins(self):
        """ Loops through any spatial joins added from config and performs the join.
        """
        prj = self.prj
        for join in self.config.SPATIAL_JOINS:
            prj.JoinSpatialTableToLayer(definition=join)


    def _sort_layers(self):
        # Sort layers
        try:
            for sort in self.config.SORT:
                self.prj.SortLayers(sort['move_layer_name'],
                                    sort['ref_layer_name'],
                                    sort['insert_position']
                                    )
        except AttributeError:
            print('\nNo Sort defined.\n')


    def _save_outputs(self):
        """  Uses output mode from to set proper output list."""
        try:
            output_mode = self.config.OUTPUT_MODE
        except AttributeError:
            print('\nWARNING:  OUTPUT_MODE not set in config.  No output saved.\n')
            return
        print('Output mode: {}'.format(output_mode))

        # FIXME:  This default is not suitable for use outside FRCC.  Should update logic to simply check for self.config.OUTPUT_LIST as the determining factor.
        if output_mode == 'Default':
            self.prj.outputs = get_default_outputs()
        elif output_mode == 'Custom':
            self.prj.outputs = self.config.OUTPUT_LIST

        # Save Outputs
        if len(self.prj.outputs) == 0:
            print('\nNo project outputs set.  Not generating any outputs.')
        else:
            self.prj.SaveOutputs()

