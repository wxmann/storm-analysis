from itertools import cycle

import pandas as pd
from pandas.util.testing import assert_frame_equal

from plotting.utils import sample_colors
from plotting.widgets import LegendBuilder

NOISE_LABEL = -1


class ClusterGroup(object):
    @classmethod
    def empty(cls):
        return cls({})

    def __init__(self, cluster_dict):
        self._cluster_dict = cluster_dict

    def __getitem__(self, item):
        return self._cluster_dict[item]

    def __contains__(self, item):
        return item in self._cluster_dict

    def __len__(self):
        if NOISE_LABEL in self._cluster_dict:
            return len(self._cluster_dict) - 1
        else:
            return len(self._cluster_dict)

    def __bool__(self):
        return len(self) > 0

    def __iter__(self):
        return iter(self.clusters)

    def numpoints(self):
        return sum(len(clust) for clust in self._unordered_clusters())

    def biggest_cluster(self):
        if len(self) == 0:
            return None
        return max(self._unordered_clusters(), key=len)

    def _unordered_clusters(self):
        return (clust for i, clust in self._cluster_dict.items() if i != NOISE_LABEL)

    @property
    def clusters(self):
        return sorted(self._unordered_clusters(),
                      key=lambda cl: (cl.begin_time, cl.end_time, len(cl)))

    @property
    def noise(self):
        return self._cluster_dict.get(NOISE_LABEL, Cluster._empty_cluster())

    def plotter(self, *args, **kwargs):
        return ClusterGroupPlotter(self, *args, **kwargs)


class Cluster(object):
    @classmethod
    def _empty_cluster(cls):
        return cls(NOISE_LABEL, pd.DataFrame(columns=['lat', 'lon', 'timestamp']), None)

    def __init__(self, cluster_num, cluster_pts, parent):
        self._index = cluster_num
        self._points = cluster_pts
        self._parent = parent

    @property
    def index(self):
        return self._index

    @property
    def pts(self):
        return self._points.copy()

    @property
    def centroid(self):
        from shapely.geometry import MultiPoint
        ctr = MultiPoint(self.latlons).centroid
        return ctr.x, ctr.y

    @property
    def latlons(self):
        return self._points[['lat', 'lon']].as_matrix()

    @property
    def events(self):
        if self._parent is None:
            return pd.DataFrame()

        return self._parent[self._parent.event_id.isin(
            self._points[self._points.cluster == self._index].event_id.unique())]

    @property
    def begin_time(self):
        return self._points.timestamp.min()

    @property
    def end_time(self):
        return self._points.timestamp.max() + pd.Timedelta('1 min')

    def __len__(self):
        return len(self._points)

    def __bool__(self):
        return self._parent is not None

    def summary(self):
        ts = self._points.timestamp
        return {
            'min_time': ts.min(),
            'max_time': ts.max(),
            'size': len(self._points),
            'time_spread': ts.max() - ts.min(),
            'center': self.centroid
        }

    def describe_tors(self, show_index=False, info=None, tz=None):
        if info is None:
            info = ['time', 'segments', 'casualties', 'minutes']

        to_join = []

        if 'time' in info:
            if self._index == NOISE_LABEL:
                time_part = '(Outliers)'
            else:
                time_part = '{} to {}'.format(self.begin_time.strftime('%Y-%m-%d %H:%M'),
                                              self.end_time.strftime('%Y-%m-%d %H:%M'))
                if tz is not None:
                    time_part += ' {}'.format(tz)
                if show_index:
                    time_part = '({}) '.format(self.index) + time_part
            to_join.append(time_part)

        stats = self.tor_stats()

        if 'segments' in info:
            ef_labels = ['EF{}'.format(f) for f in range(0, 6)]
            ef_parts = ['{}: {}'.format(label, stats[label.lower()]) for label in ef_labels]
            if stats['ef?']:
                ef_parts.append('EF?: {}'.format(stats['ef?']))

            segments_part = '{} segments ({})'.format(stats['segments'], ', '.join(ef_parts))
            to_join.append(segments_part)

        if 'casualties' in info:
            casualty_part = '{} fatalities | {} injuries'.format(stats['fatalities'], stats['injuries'])
            to_join.append(casualty_part)

        if 'minutes' in info:
            length_part = '{} tornado minutes'.format(len(self))
            to_join.append(length_part)

        return '\n'.join(to_join)

    def tor_stats(self):
        if self._parent is None:
            raise NotImplementedError("Cannot output tornado stats for empty cluster")

        all_events = self.events
        tor_events = all_events[all_events.event_type == 'Tornado']
        tor_ef = tor_events.stevent_tor.ef()
        tor_longevity = tor_events.stevent_tor.longevity()

        ret = {'ef{}'.format(i): tor_ef[tor_ef == i].count() for i in range(0, 6)}
        ret['ef?'] = tor_ef[tor_ef.isnull()].count()
        ret['segments'] = len(tor_events)
        ret['total_time'] = tor_longevity.sum()
        ret['fatalities'] = tor_events.deaths_direct.sum()
        ret['injuries'] = tor_events.injuries_direct.sum()

        return ret

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, Cluster):
            return False

        try:
            assert_clusters_equal(self, other)
            return True
        except AssertionError:
            return False


def assert_clusters_equal(clust1, clust2):
    clust1_pts = clust1.pts.copy()
    clust2_pts = clust2.pts.copy()
    clust1_pts.reset_index(drop=True, inplace=True)
    clust2_pts.reset_index(drop=True, inplace=True)
    clust1_pts.drop('cluster', inplace=True, axis=1)
    clust2_pts.drop('cluster', inplace=True, axis=1)

    assert_frame_equal(clust1_pts, clust2_pts)

    clust1_evts = clust1.events.copy()
    clust2_evts = clust2.events.copy()
    clust1_evts.reset_index(drop=True, inplace=True)
    clust2_evts.reset_index(drop=True, inplace=True)

    assert_frame_equal(clust1_evts, clust2_evts)


class ClusterGroupPlotter(object):
    def __init__(self, cluster_group, bgmap, colors,
                 plot_noise=True, noise_color='gray', tz='CST'):
        self._cluster_group = cluster_group
        self._grouplen = len(cluster_group)
        self._bgmap = bgmap
        self._colors = colors
        self._noise_color = noise_color if plot_noise else None
        self._plot_noise = plot_noise
        self._tz = tz

    def _get_colors(self, colors=None):
        colors = colors or self._colors
        if isinstance(colors, str):
            return sample_colors(self._grouplen, colors)
        if isinstance(colors, (list, tuple)):
            return cycle(colors)
        return colors

    def tornadoes(self, linewidth=2, shadow=True):
        colors = self._get_colors()
        for clust, color in zip(self._cluster_group.clusters, colors):
            clust.events.stevent_plot.tornadoes(self._bgmap, color=color,
                                                linewidth=linewidth, shadow=shadow)
        if self._plot_noise:
            noise = self._cluster_group.noise
            noise.events.stevent_plot.tornadoes(self._bgmap, color=self._noise_color,
                                              linewidth=linewidth, shadow=shadow)

    def hail(self, marker='+', markersize=2, shadow=False, colors=None):
        colors = self._get_colors(colors)
        for clust, color in zip(self._cluster_group.clusters, colors):
            clust.events.stevent_plot.hail(self._bgmap, color=color,
                                           marker=marker, markersize=markersize, shadow=shadow)
        if self._plot_noise:
            noise = self._cluster_group.noise
            noise.events.stevent_plot.hail(self._bgmap, color=self._noise_color,
                                           marker=marker, markersize=markersize, shadow=shadow)

    def legend(self, info=None):
        colors = self._get_colors()
        legend = LegendBuilder(ax=self._bgmap.ax)

        for clust, color in zip(self._cluster_group.clusters, colors):
            legend.append(color, clust.describe_tors(tz=self._tz, info=info))

        if self._plot_noise:
            noise = self._cluster_group.noise
            legend.append(self._noise_color, noise.describe_tors(tz=self._tz, info=info))

        legend.plot_legend()
