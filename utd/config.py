
import os

CONFIG_DIR = os.path.expanduser(os.path.join('~', '.utd'))
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.py')

netid = None

import getpass

def get_password():
    global netid
    return getpass.getpass('Password for {}: '.format(config.netid))

if os.path.exists(CONFIG_FILE):
    import importlib.util
    spec = importlib.util.spec_from_file_location("config", CONFIG_FILE)
    config = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config)

    netid = getattr(config, 'netid', netid)
    get_password = getattr(config, 'get_password', get_password)

