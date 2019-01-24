
from . import config
from . import util

from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from datetime import datetime, timedelta
import time
import tempfile
import os
import getpass
from random import random
from glob import glob
import shutil
import atexit

import logging
_logger = logging.getLogger(__name__)

BASE_URL = 'https://elearning.utdallas.edu'

LAST_API_CALL = datetime.min

LOGIN = {}

TMPDIR = tempfile.TemporaryDirectory()

@atexit.register
def _TMPDIR_remove():
    TMPDIR.cleanup()

from functools import wraps

def _ratelimit(t0, a=1, b=1):
    t1 = datetime.now()
    dr = timedelta(seconds = a + b * random())
    dt = t1 - t0
    if dt < dr:
        time.sleep((dr - dt).total_seconds())

def ratelimit(f, a=1, b=1):
    @wraps(f)
    def g(*args, **kw):
        global LAST_API_CALL
        _ratelimit(LAST_API_CALL, a=a, b=b)
        x = f(*args, **kw)
        LAST_API_CALL = datetime.now()
        return x
    return g

@ratelimit
def _login(netid, get_password):
    global LOGIN
    if netid in LOGIN:
        return LOGIN[netid]

    _logger.info('Preparing to log-in to {}', BASE_URL)

    password = get_password()

    options = webdriver.ChromeOptions()
    options.add_argument('disable-java')
    options.add_experimental_option('prefs', 
                    {
                        'download.default_directory': os.getcwd(),
                        'download.prompt_for_download': False,
                        'download.directory_upgrade': True,
                        'plugins.always_open_pdf_externally': True,
                    }
                ) 
    driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)
    driver.implicitly_wait(30)

    driver.get(BASE_URL)

    username_element = driver.find_element_by_id("netid")
    password_element = driver.find_element_by_id("password")
    login_button     = driver.find_element_by_id("submit")
    
    username_element.clear()
    password_element.clear()

    username_element.send_keys(netid)
    password_element.send_keys(password)
    login_button.click()

    # cookie button
    agree_button = driver.find_element_by_id("agree_button")
    agree_button.click()

    LOGIN[netid] = driver

    return driver

import atexit

@atexit.register
def _logout():
    for x in LOGIN:
        LOGIN[x].quit()

@ratelimit
def _to_url(driver, url):
    driver.get(url)

@ratelimit
def _find_link_text_and_click(driver, link_text):
    link = driver.find_element_by_link_text(link_text)
    link.click()

@ratelimit
def _find_by_id_and_click(driver, id):
    el = driver.find_element_by_id(id)
    el.click()

@ratelimit
def _find_by_name_and_click(driver, name):
    el = driver.find_element_by_name(name)
    el.click()

@ratelimit
def _find_by_id_and_send_keys(driver, id, keys):
    el = driver.find_element_by_id(id)
    el.send_keys(keys)

@ratelimit
def download(netid: str, get_password, link_text: str) -> str:

    pattern = 'gc_*_fullgc_*.csv'

    F0 = set(glob(pattern))

    driver = _login(netid, get_password)
    _to_url(driver, BASE_URL)
    _find_link_text_and_click(driver, link_text)
    _find_link_text_and_click(driver, 'Grade Center')
    _find_link_text_and_click(driver, 'Full Grade Center')
    _find_link_text_and_click(driver, 'Work Offline')
    _find_link_text_and_click(driver, 'Download')
    _find_by_id_and_click(driver, 'delimiterComma')
    _find_by_id_and_click(driver, 'hiddenYes')
    _find_by_id_and_click(driver, 'bottom_Submit')
    _find_link_text_and_click(driver, 'DOWNLOAD')

    for i in range(20):
        time.sleep(1)
        F1 = set(glob(pattern))
        dF = F1 - F0
        if dF: break
    else:
        raise Exception('Failed to download: {}'.format(pattern))

    x = dF.pop()

    return x

from csv import DictReader

KEY = 'Username'

@ratelimit
def upload(netid: str, get_password, link_text: str, path: str) -> None:

    with open(path, 'r') as r:
        X = [x for x in r.readlines() if x.strip()]
        if len(X) == 0:
            _logger.info('Upload file is empty, skipping: {}', path)
            return

    with open(path, 'r') as r:
        reader = DictReader(r)
        if not (KEY in reader.fieldnames):
            msg = 'Key column `{}` missing: {}'.format(KEY, path)
            _logger.error(msg)
            raise Exception(msg)
        rows = list(reader)
        if len(rows) == 0:
            _logger.info('Upload file contains no rows, skipping: {}', path)
            return

    driver = _login(netid, get_password)
    _to_url(driver, BASE_URL)
    _find_link_text_and_click(driver, link_text)
    _find_link_text_and_click(driver, 'Grade Center')
    _find_link_text_and_click(driver, 'Full Grade Center')
    _find_link_text_and_click(driver, 'Work Offline')
    _find_link_text_and_click(driver, 'Upload')
    elem = driver.find_element_by_id('theFile_chooseLocalFile')
    elem.send_keys(os.path.abspath(path))
    _find_by_id_and_click(driver, 'bottom_Submit')
    _find_by_name_and_click(driver, 'bottom_Submit')

@ratelimit
def webassign(netid: str, get_password, link_text: str) -> None:

    driver = _login(netid, get_password)
    _to_url(driver, BASE_URL)
    _find_link_text_and_click(driver, link_text)
    _find_link_text_and_click(driver, 'Course Tools')
    _find_link_text_and_click(driver, 'WebAssign')
    _find_link_text_and_click(driver, 'Export Roster')
    _find_link_text_and_click(driver, 'Import Grades')

