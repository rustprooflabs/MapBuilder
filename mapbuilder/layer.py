""" The layer module contains a Layer class to help when working with layers."""

class Layer(object):

    def __init__(self, definition):
        # Name -- Required
        try:
            self.name = definition['name']
        except KeyError:
            raise KeyError('The "name" key is required for the Layer object.')

        # Path -- Required
        try:
            self.path = definition['path']
        except KeyError:
            raise KeyError('The "path" key is required for the Layer object.')

        # Style - Optional - If provided it should be a filename in the project's directory.
        try:
            self.style = definition['style']
        except KeyError:
            self.style = None

        # Set visible status for layers
        try:
            self.visible = definition['visible']
        except KeyError:
            self.visible = True

        # Sets Definition query to allow filtering layers based on data attributes
        try:
            self.definition_query = definition['definition_query']
        except KeyError:
            self.definition_query = None    

