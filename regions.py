import pandas as pd
from shapely.geometry import Polygon

import config

CHASE_ALLEY = config.get_resource('chasealley.csv')

SOUTH_CHASE_ALLEY = config.get_resource('south_chasealley.csv')

CORE_PLAINS = config.get_resource('coreplains.csv')


def load_region(file):
    bdys_df = pd.read_csv(file)
    # depending on the version of shapely, we might have to manually close the polygon
    bdys_df = bdys_df.append(bdys_df.loc[0])
    latlon_mat = bdys_df[['lat', 'lon']].values
    return bdys_df, Polygon(latlon_mat)