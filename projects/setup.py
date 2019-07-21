import sys
sys.path.append('..')

import config
from shared import workdir as _workdir

def setup_project_env(workdir=None):
    rootdir = config.ROOT_PROJECT_DIR

    import sys
    sys.path.append(rootdir)

    if workdir:
        _workdir.setto(workdir)