import pandas as pd
import numpy as np

@pd.api.extensions.register_dataframe_accessor('stevent_plot')
class StormEventsPlot(object):
    def __init__(self, df):
        self._df = df

    def tornadoes(self, cartopymap, color='gray', shadow=False, **kwargs):
        for _, event in self._df.iterrows():
            if event.event_type == 'Tornado':
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
