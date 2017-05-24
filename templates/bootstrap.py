import sys

# Set as path to MapBuilder directory.
sys.path.insert(0, 'C:\\Path\\To\\MapBuilder')
from controller import Controller

# Instantiate a Controller to run the automation
c = Controller()

##############################################
# Setup Basic configuration options
##############################################

# Project path:  Where to save and find files?
c.config.PROJECT_BASE_PATH = 'C:\\Path\\To\\Project\\Directory'

# Name of Project - Used for base file name for project's MXD
c.config.PROJECT_NAME = 'Project Name Goes Here'

# Path to template MXD file
c.config.TEMPLATE_MXD = 'C:\\Path\\To\\Template.mxd'


# Create dictionary w/ Bounding box options for output
frcc_service_area = {'name': 'FRCC Service Area', # Used in file name, and in 3rd header
                     'xmin': -106.103, # Minimum "x" (longitude)
                     'ymin': 39.844, # Minimum "y" (latitude)
                     'xmax': -103.541, # Maximum "x" (longitude)
                     'ymax': 41.015} # Maximum "y" (latitude)


c.config.OUTPUT_MODE = 'Custom'

# OUTPUT_LIST requires a List of Dictionaries.
c.config.OUTPUT_LIST = [frcc_service_area]

# Runs MapBuilder
c.run()



