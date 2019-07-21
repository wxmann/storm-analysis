import matplotlib.patheffects as path_effects
import cartopy.crs as ccrs

class CartopyMapPlotter(object):
    def __init__(self, cartopymap):
        self._bgmap = cartopymap

    def lines(self, latlons, color, shadow=False, **kwargs):
        if not latlons.any():
            return
        else:
            use_kw = kwargs
            ispoint = latlons.shape[0] == 1

            if ispoint:
                # a line plot will cause a singular point to vanish, so we force it to
                # plot points here
                use_kw = use_kw.copy()
                use_kw.pop('linestyle', None)
                size = use_kw.pop('linewidth', 2)
                use_kw['marker'] = 'o'
                use_kw['markersize'] = size
                use_kw['markeredgewidth'] = 0.0

            if shadow:
                shadow_kw = dict(offset=(0.5, -0.5), alpha=0.6)
                if ispoint:
                    shadow_effect = path_effects.SimplePatchShadow(**shadow_kw)
                else:
                    shadow_effect = path_effects.SimpleLineShadow(**shadow_kw)

                use_kw['path_effects'] = [shadow_effect, path_effects.Normal()]

            self._bgmap.ax.plot(latlons[:, 1], latlons[:, 0],
                                color=color, transform=ccrs.PlateCarree(), **use_kw)

    def points(self, latlons, color='k', marker='o', markersize=2, shadow=False, **kwargs):
        lons = latlons[:, 1]
        lats = latlons[:, 0]

        kw = kwargs.copy()
        if shadow:
            # TODO: fix breaking shadow effects
            shadow_kw = dict(offset=(0.5, -0.5), alpha=0.6)
            shadow_effect = path_effects.SimplePatchShadow(**shadow_kw)
            kw['path_effects'] = [shadow_effect, path_effects.Normal()]

        self._bgmap.ax.scatter(lons, lats, marker=marker, s=markersize,
                            transform=ccrs.PlateCarree(), facecolor=color, **kw)
