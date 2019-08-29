import pandas as pd

def btk(storm_id, convert_cols=True):
    link = f'https://ftp.nhc.noaa.gov/atcf/btk/b{storm_id}.dat'
    cols = [
        'basin', 'cy', 'yyyymmddhh', 'technum', 'tech', 'tau', 'lat', 'lon',
        'vmax', 'mslp', 'ty', 'rad', 'windcode', 'rad1', 'rad2', 'rad3', 'rad4',
        'pouter', 'router', 'rmw', 'gusts', 'eye', 'subregion', 'maxseas', 'initials',
        'dir', 'speed', 'stormname', 'depth', 'seas', 'seascode', 'seas1', 'seas2',
        'seas3', 'seas4', 'userdefine1', 'userdata1', 'userdefine2', 'userdata2',
        'userdefine3', 'userdata3', 'userdefine4', 'userdata4', 'userdefine5', 'userdata5'
    ]

    ret = pd.read_csv(link, header=None, names=cols, dtype={'yyyymmddhh': str})

    if convert_cols:
        ret['lat'] = pd.to_numeric(ret.lat.str[:-1]) * ret.lat.apply(lambda r: 1 if r[-1] == 'N' else -1) / 10
        ret['lon'] = pd.to_numeric(ret.lon.str[:-1]) * ret.lon.apply(lambda r: 1 if r[-1] == 'E' else -1) / 10
        ret['ts'] = pd.to_datetime(ret.yyyymmddhh.str.strip(), format='%Y%m%d%H')

    return ret
