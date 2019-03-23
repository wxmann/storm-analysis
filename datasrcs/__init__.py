# hook into custom accessors
from .ops import (
    TemporalDataframe as _temporalhook,
    GeospatialDataframe as _geospatialhook
)

__all__ = ['spc', 'ops']