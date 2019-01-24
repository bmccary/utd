
import os

CONFIG_DIR = os.path.expanduser(os.path.join('~', '.utd'))
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.py')

NETID = None

from getpass import getpass

def get_password(netid=NETID):
    if netid:
        prompt = 'Password for {}: '.format(netid)
    else:
        prompt = 'Password: '
    return getpass(prompt)

import logging
_logger = logging.getLogger(__name__)

if os.path.exists(CONFIG_FILE):
    _logger.info('Config file found: {}', CONFIG_FILE)
    import importlib.util
    spec = importlib.util.spec_from_file_location("config", CONFIG_FILE)
    config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)

    NETID = getattr(config, 'netid', NETID)
    get_password = getattr(config, 'get_password', get_password)
else:
    _logger.info('Config file not found: {}', CONFIG_FILE)

