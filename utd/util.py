
import os
import errno

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

from . import config

import shlex
from subprocess import check_output

def get_password_eval(command):
    args = shlex.split(command)
    y = check_output(args).splitlines()[0]
    return y.decode('utf-8')

