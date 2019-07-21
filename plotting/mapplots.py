import matplotlib.patheffects as path_effects
import cartopy.crs as ccrs

class CartopyMapPlotter(object):
    def __init__(self, cartopymap):
        self.bgmap = cartopymap

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

            self.bgmap.ax.plot(latlons[:, 1], latlons[:, 0],
                               color=color, transform=ccrs.PlateCarree(), **use_kw)