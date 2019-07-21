import pandas as pd
import numpy as np

from algs.corrections import correct_tornado_times

@pd.api.extensions.register_dataframe_accessor('stevent_plot')
class StormEventsPlot(object):
    def __init__(self, df):
        self._df = df

    def tornadoes(self, cartopymap, color='red', shadow=False, **kwargs):
        torevents = self._df[self._df.event_type == 'Tornado']
        for _, event in torevents.iterrows():
            pt1 = [event.begin_lat, event.begin_lon]
            pt2 = [event.end_lat, event.end_lon]
            if pt1 == pt2:
                # the `plot_lines` function uses the shape of the array as a cue
                # to use a point or a line. We don't want to draw a line when there is
                # is only one point in the tornado.
                arr = np.array([pt1])
            else:
                arr = np.array([pt1, pt2])

            cartopymap.plot.lines(arr, color, shadow=shadow, **kwargs)

    def hail(self, cartopymap, color='green', marker='+', markersize=2,
             shadow=False, **kwargs):
        hailevents = self._df[self._df.event_type == 'Hail']
        pts = hailevents[['begin_lat', 'begin_lon']].values
        cartopymap.plot.points(pts, color, marker=marker, markersize=markersize,
                               shadow=shadow, **kwargs)


@pd.api.extensions.register_dataframe_accessor('stevent_tor')
class StormEventsTorOps(object):
    def __init__(self, df):
        self._df = df

    def longevity(self):
        return self._df.end_date_time - self._df.begin_date_time

    def ef(self):
        frating = self._df.tor_f_scale.str.replace(r'\D', '')
        return pd.to_numeric(frating, errors='coerce')

    def speed_mph(self, floor_longevity=None):
        if floor_longevity is None:
            floor_longevity = pd.Timedelta(seconds=30)

        longevities = self.longevity()
        longevities[longevities < floor_longevity] = np.nan
        longevities = pd.to_timedelta(longevities)
        longevities /= pd.Timedelta('1 hour')
        path_lens = self._df['tor_length']

        return path_lens / longevities

    def correct_tornado_times(self, copy=True):
        return correct_tornado_times(self._df, copy)
