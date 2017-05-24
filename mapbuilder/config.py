""" Config module contains config class used to define how maps are generated."""

class Config:
    """ Turning into a class to allow cycling through external parameters."""
    def __init__(self):

        # PROJECT_NAME determines name of target MXD file.
        # No Spaces or special characters in Project Name!
        self.PROJECT_NAME = 'Default_MapBuilder_Project_Name'

        self.PROJECT_AUTHOR = 'Unknown Author'
        self.PROJECT_DESCRIPTION = None

        # PROJECT_BASE_PATH determines where project files are saved.
        # NOTE:  Double slashes is safer, sometimes you can get away with single
        #      but this is a good habit.
        self.PROJECT_BASE_PATH = 'C:\\ArcGIS\\Tmp'

        # Sets Text to add to header of output files (PDF)
        self.OUTPUT_HEADER_PREFIX = 'This map was generated using the MapBuider Module.'

        # Prefixed to the output file name.
        self.OUTPUT_FILE_PREFIX = 'MapBuilder_Output'

        # Set Legend position for Output
        ## Note:  These need to be manually adjusted based on the length of the names in legend.
        self.LEGEND_X = 8.8858
        self.LEGEND_Y = 0.3768

        # Start with empty lists for optional parameters
        self.TABLES = list()
        self.LAYERS = list()
        self.SPATIAL_JOINS = list()
        self.SORT = list()

        # Local Geocoder Location
        self.ADDRESS_LOCATOR = "C:\\ArcGIS\\Locator_2010\\Street_Addresses_US.loc"
