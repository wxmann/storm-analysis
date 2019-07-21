from functools import partial

import numpy as np
import pandas as pd
from geopy.distance import great_circle
from sklearn.cluster import DBSCAN
from sklearn.metrics import pairwise_distances

from .cluster_api import NOISE_LABEL, ClusterGroup, Cluster
from .discretize import discretize


def st_clusters(events, eps_km, eps_min, min_samples, algorithm=None):
    assert min_samples > 0

    if events.empty:
        raise ValueError('Cannot cluster empty events')

    if algorithm == 'brute':
        cluster_dict = _brute_st_clusters(events, eps_km, eps_min, min_samples)
    else:
        points = discretize(events)
        points = points[(~points.lon.isnull()) & (~points.lat.isnull())]

        if points.empty:
            raise ValueError('Cannot cluster empty events')

        pairwise_distance_input = points[['lat', 'lon']]
        pairwise_distance_input['timestamp_sec'] = points.timestamp.astype(np.int64) / 10 ** 9
        binary_dist_metric = partial(_boolean_distance, eps_km=eps_km, eps_min=eps_min)
        n_jobs = 1 if len(points) < 100 else -1

        binary_dists = pairwise_distances(pairwise_distance_input,
                                          metric=binary_dist_metric, n_jobs=n_jobs)

        db = DBSCAN(eps=0.5, metric='precomputed', min_samples=min_samples)
        cluster_labels = db.fit_predict(binary_dists)

        points['cluster'] = cluster_labels
        cluster_dict = {label: Cluster(label, points[points.cluster == label], events)
                        for label in points.cluster.unique()}

    return ClusterGroup(cluster_dict)


def _boolean_distance(pt1, pt2, eps_km, eps_min):
    lat_index = 0
    lon_index = 1
    timestamp_sec_index = 2
    sec_per_min = 60
    return abs(pt1[timestamp_sec_index] - pt2[timestamp_sec_index]) > eps_min * sec_per_min or \
           great_circle((pt1[lat_index], pt1[lon_index]), (pt2[lat_index], pt2[lon_index])).km > eps_km


def _brute_st_clusters(events, eps_km, eps_min, min_samples):
    points = discretize(events)
    noise = NOISE_LABEL
    undetermined = -999

    label = 0
    points['cluster'] = undetermined
    neighb_threshold = min_samples - 1
    clusterpts = set()
    noisepts = set()

    def is_noise(group, threshold):
        return group.shape[0] < threshold

    for index in points.index:
        if index in clusterpts or index in noisepts:
            continue

        neighb = _neighbors(points, eps_km, eps_min, index)
        if is_noise(neighb, neighb_threshold):
            points.set_value(index, 'cluster', noise)
            noisepts.add(index)
        else:
            label += 1
            points.set_value(index, 'cluster', label)
            clusterpts.add(index)
            subpts = {i for i in neighb.index if i not in clusterpts}

            while subpts:
                qindex = subpts.pop()
                if qindex in noisepts:
                    points.set_value(qindex, 'cluster', label)
                    noisepts.remove(qindex)
                    clusterpts.add(qindex)

                if qindex in clusterpts:
                    continue

                points.set_value(qindex, 'cluster', label)
                clusterpts.add(qindex)
                neighb_inner = _neighbors(points, eps_km, eps_min, qindex)

                if not is_noise(neighb_inner, neighb_threshold):
                    subpts = subpts.union({i for i in neighb_inner.index if i not in clusterpts})

    clusters = {}
    for clust_label in points.cluster.unique():
        clust_points = points[points.cluster == clust_label]
        clusters[clust_label] = Cluster(clust_label, clust_points, events)

    noise_points = points[points.cluster == noise]
    clusters[noise] = Cluster(noise, noise_points, events)
    return clusters


def _neighbors(df, spatial_dist, temporal_dist, index):
    pt = df.loc[index]
    tmin = pt.timestamp - pd.Timedelta(minutes=temporal_dist)
    tmax = pt.timestamp + pd.Timedelta(minutes=temporal_dist)

    filtered = df[(df.timestamp >= tmin) & (df.timestamp <= tmax)]
    mask = filtered.apply(lambda r: great_circle((r.lat, r.lon), (pt.lat, pt.lon)).km, axis=1) < spatial_dist
    return filtered[mask & (filtered.index != pt.name)]