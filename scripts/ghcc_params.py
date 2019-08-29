import warnings

_default_params = {
    'map': 'standard',
    'zoom': 1,
    'past': 0,
    'colorbar': 0,
    'mapcolor': 'black',
    'quality': 90,
    'width': 1200,
    'height': 900,
    'type': 'Image'
}

_zoom_dict = {
    1: 'high',
    2: 'med',
    4: 'low'
}


def location_info(params):
    if 'x' in params and 'y' in params:
        x, y = params['x'], params['y']
    elif 'lat' in params and 'lon' in params:
        x, y = params['lat'], params['lon']
    else:
        raise ValueError("Params must have either x,y or lat,lon")
    return x, y


def sattype(params):
    if 'info' in params:
        # assume GOES legacy which requires info param
        sattype = params['info'].upper()
    else:
        # assume GOES-R and presence of channel information
        sattype = 'Ch{}'.format(params['satellite'][-2:])

    return sattype


def zoom(params):
    return _zoom_dict[params['zoom']]


def with_defaults(params):
    result = params.copy()
    for k in _default_params:
        if k not in result:
            result[k] = _default_params[k]
    return result


def to_params(satellite, position, uselatlon, info=None, **kwargs):
    if len(position) != 2:
        raise ValueError("Position must be an x,y or lat,lon pair")

    params = kwargs.copy()
    for k in _default_params:
        if k not in params:
            params[k] = _default_params[k]

    params['satellite'] = satellite

    if uselatlon:
        params['lat'], params['lon'] = position[0], position[1]
    else:
        params['x'], params['y'] = position[0], position[1]
    if info is not None:
        params['info'] = info

    if params['type'] != 'Image':
        warnings.warn('Only Image type supported at this time. Default to Image type')
        params['type'] = 'Image'

    return params