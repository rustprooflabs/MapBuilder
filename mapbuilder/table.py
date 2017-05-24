""" The table module contains a Table class to help when working with data
tables containing no spatial data.
"""

class Table(object):

    def __init__(self, definition):
        """ Pulls values from `definition` and sets default values where necessary.

        Values:
            * name
            * path
            * join
            * geocode
            * geocode_layer_name
            * geocode_layer_style
            * layer_visible
        """

        try:
            self.name = definition['name']
        except KeyError:
            raise KeyError('The "name" key is required for the Table object.')


        try:
            self.path = definition['path']
        except KeyError:
            raise KeyError('The "path" key is required for the Table object.')


        try:
            self.join = definition['join']
        except KeyError:
            self.join = False


        try:
            self.geocode = definition['geocode']
        except KeyError:
            self.geocode = False


        try:
            self.geocoded_layer_name = definition['geocoded_layer_name']
        except KeyError:
            self.geocoded_layer_name = self.name + '_Geocoded'


        try:
            self.geocode_layer_style = definition['geocode_layer_style']
        except KeyError:
            self.geocode_layer_style = None

        self.visible = definition['visible']
