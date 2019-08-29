import warnings
import urllib.parse as urlparse

import re
from datetime import datetime, timedelta

from .helpers import get_image_srcs
from .request import http_stream, s3_put
from .ghcc_params import location_info, zoom, sattype

NASA_MSFC_BASE_URL = 'https://weather.msfc.nasa.gov'

GOES_16_BASE_URL = urlparse.urljoin(NASA_MSFC_BASE_URL, '/cgi-bin/get-abi')

GOES_LEGACY_BASE_URL = urlparse.urljoin(NASA_MSFC_BASE_URL, '/cgi-bin/get-goes')


def create_filename(params, img_ts):
    template = 'GHCC_{sattype}_{zoom}_{datetime}_({x},{y}).jpg'
    x, y = location_info(params)
    img_file = template.format(zoom=zoom(params),
                               x=x,
                               y=y,
                               sattype=sattype(params),
                               datetime=img_ts.strftime('%Y%m%d_%H%M'))
    return img_file



def ghcc_save(params, to_bucket, timefilter=None):
    page_response = http_stream(GOES_16_BASE_URL, queryparams=params)
    img_response, img_ts = fetch_img_from_response(page_response, timefilter)
    filename = create_filename(params, img_ts)

    with img_response:
        s3_put(to_bucket, key=filename, content=img_response.content)


def fetch_img_from_response(response, timefilter=None):
    goes_jpg_filter = lambda img: 'GOES' in img and '.jpg' in img
    img_urls = get_image_srcs(response.text, goes_jpg_filter)

    if not img_urls:
        raise SaveException(
            "Cannot parse an image URL for response. Text of response: \n\n{}".format(response.text))

    img_url_to_save = urlparse.urljoin(NASA_MSFC_BASE_URL, img_urls[0])
    img_ts = _extract_time_from_url(img_url_to_save)

    if timefilter and not timefilter(img_ts):
        warnings.warn('Image with time: {} did not pass filter, skipping'.format(img_ts))
        raise SaveTermination

    return http_stream(img_url_to_save), img_ts


def _extract_time_from_url(url):
    regex = 'GOES(\d{2})(\d{2})(\d{4})(\d{1,3})(.{6})\.jpg'
    found = re.search(regex, url)
    if not found:
        raise SaveException("Cannot find date-time for file: {0}".format(url))

    found_hour = int(found.group(1))
    found_min = int(found.group(2))
    found_year = int(found.group(3))
    found_dayofyr = int(found.group(4))

    day_before_year = datetime(year=found_year - 1, month=12, day=31)
    current_day = day_before_year + timedelta(days=found_dayofyr)

    return datetime(year=found_year, month=current_day.month, day=current_day.day,
                    hour=found_hour, minute=found_min)


class SaveException(Exception):
    pass


class SaveTermination(Exception):
    pass