from shared import workdir
from stormevents.io import load_tornadoes

if __name__ == '__main__':
    workdir.setto('~/weatherpy-work')
    results, df = load_tornadoes('1985-01-01 00:00', '1985-12-31 00:00', tz='CST', debug=True)