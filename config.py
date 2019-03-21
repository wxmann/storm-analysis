import os

ROOT_PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))

RESOURCES_DIR = os.path.join(ROOT_PROJECT_DIR, 'resources')

SHAPEFILE_DIR = os.path.join(RESOURCES_DIR, 'shp')


def get_shp(directory, name):
    return os.path.join(SHAPEFILE_DIR, directory, name)