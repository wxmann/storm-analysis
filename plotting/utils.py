import matplotlib.colors as mcolors
import matplotlib.cm as cm

## Color sampling

def sample_colors(n, src_cmap):
    return ColorSamples(n, src_cmap)


# inspired from http://qingkaikong.blogspot.com/2016/08/clustering-with-dbscan.html
class ColorSamples(object):
    def __init__(self, n_samples, cmap):
        self.n_samples = n_samples
        color_norm = mcolors.Normalize(vmin=0, vmax=self.n_samples - 1)
        self.scalar_map = cm.ScalarMappable(norm=color_norm, cmap=cmap)

        self._iter_index = 0

    def __getitem__(self, item):
        return self.scalar_map.to_rgba(item)

    def __iter__(self):
        while self._iter_index < self.n_samples:
            yield self.scalar_map.to_rgba(self._iter_index)
            self._iter_index += 1

        self._iter_index = 0

    def __len__(self):
        return self.n_samples