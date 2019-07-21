import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

class LegendBuilder(object):
    def __init__(self, ax=None, **legend_kw):
        self.handles = []
        self._ax = ax
        self.legend_kw = legend_kw

    def append(self, color, label, **kwargs):
        self.handles.append(mpatches.Patch(color=color, label=label, **kwargs))

    @property
    def ax(self):
        return self._ax or plt.gca()

    def plot_legend(self):
        self.ax.legend(handles=self.handles, **self.legend_kw)