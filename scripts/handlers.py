from .position import satellite_position
from .ghcc_params import with_defaults
from .ghcc import ghcc_save

"""
example event JSON:
{
    "storm_id": "al052019",
    "params": {
        "satellite": "GOESEastconusband13",
        "zoom": 1,
        "width": 1200,
        "height": 900,
        "palette": "ir10.pal"
    },
    "s3_bucket": "hurricane-bucket"
}
"""

def ghcc_satellite(event, context):
    storm_id = event['storm_id']

    params = with_defaults(event['params'])
    lat, lon = satellite_position(storm_id)
    params['lat'] = lat
    params['lon'] = lon

    ghcc_save(params, to_bucket=event['s3_bucket'])
