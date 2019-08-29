import pandas as pd
from datasrcs import atcf

def satellite_position(storm_id):
    records = atcf.btk(storm_id)
    return calc_center(records)


def calc_center(records):
    maxtime = records.ts.max()
    prevtime = records.ts.max() - pd.Timedelta('6 hr')

    maxtimelatlon = records[records.ts == maxtime].head(1)[['lat', 'lon']].values
    prevtimelatlon = records[records.ts == prevtime].head(1)[['lat', 'lon']].values

    current_time = pd.Timestamp.utcnow()
    ret = maxtimelatlon

    if current_time - maxtime.tz_localize('UTC') > pd.Timedelta('3 hr'):
        ret = maxtimelatlon + (maxtimelatlon - prevtimelatlon) / 2

    return ret[0]