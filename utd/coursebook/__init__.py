
from .. import config
from .. import util

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

MODULE_NAME = __name__.split('.')[-1]

DOT_MODULE = os.path.join(config.CONFIG_DIR, MODULE_NAME)
DOT_MODULE_CACHE = os.path.join(DOT_MODULE, 'cache')
DOT_MODULE_CACHE_ROSTER = os.path.join(DOT_MODULE_CACHE, 'roster')
DOT_MODULE_CACHE_SEARCH = os.path.join(DOT_MODULE_CACHE, 'search')
DOT_MODULE_CACHE_ALIAS = os.path.join(DOT_MODULE_CACHE, 'alias')

URL = 'https://coursebook.utdallas.edu'
LOGIN_URL = URL + '/login/coursebook'
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

    print('\n'*4)
    print('Preparing to log-in to ', URL)
    print('\n'*4)
    password = get_password()

    options = webdriver.ChromeOptions()
    options.add_argument('disable-java')
    options.add_experimental_option('prefs', 
                    {
                        'download.default_directory': TMPDIR.name,
                        'download.prompt_for_download': False,
                        'download.directory_upgrade': True,
                        'plugins.always_open_pdf_externally': True,
                    }
                ) 
    driver = webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)
    driver.implicitly_wait(30)

    driver.get(LOGIN_URL)

    username_element = driver.find_element_by_id("netid")
    password_element = driver.find_element_by_id("password")
    login_button     = driver.find_element_by_id("login-button")
    
    username_element.clear()
    password_element.clear()

    username_element.send_keys(netid)
    password_element.send_keys(password)
    login_button.click()

    LOGIN[netid] = driver

    return driver

import atexit

@atexit.register
def _logout():
    for x in LOGIN:
        LOGIN[x].quit()


ROSTER_FORMAT = ['pdf', 'xlsx', 'json',]

ROSTER_PDF_URL = URL + '/prosterpdf/{prefix}{number}.{section}.{term}'
ROSTER_PDF_PATTERN = '{prefix}{number}.{section}.{term}'

ROSTER_XLSX_URL = URL + '/reportmonkey/class_roster/{prefix}{number}.{section}.{term}/excel'
ROSTER_XLSX_PATTERN = 'roster-{prefix}{number}.{section}.{term}-*.xlsx'

ROSTER_JSON_URL = URL + '/reportmonkey/class_roster/{prefix}{number}.{section}.{term}/json'
ROSTER_JSON_PATTERN = 'roster-{prefix}{number}.{section}.{term}-*.json'

@ratelimit
def roster_download(netid: str, get_password, address: str, format: str, new: bool = False) -> str:
    if not format in ROSTER_FORMAT:
        raise Exception('Expected :format to be one of: {}'.format(ROSTER_FORMAT))
    if not new:
        cache = sorted(glob(os.path.join(DOT_MODULE_CACHE_ROSTER, address, '*.' + format)))
        if cache:
            return cache[-1]
    term, prefix, number, section = address.split('-')
    d = dict(term=term, prefix=prefix, number=number, section=section)
    driver = _login(netid, get_password)
    f2t = {
            'pdf': (ROSTER_PDF_URL, ROSTER_PDF_PATTERN),
            'xlsx': (ROSTER_XLSX_URL, ROSTER_XLSX_PATTERN),
            'json': (ROSTER_JSON_URL, ROSTER_JSON_PATTERN),
        }
    url_template, pattern_template = f2t[format]
    url = url_template.format(**d)
    pattern = os.path.join(TMPDIR.name, pattern_template.format(**d))

    driver.get(url)

    # For reasons unclear to me, this is necessary.
    if format in ['pdf',]:
        driver.refresh()

    for i in range(20):
        time.sleep(1)
        x0 = set(glob(pattern))
        if x0: break
    else:
        raise Exception('Failed to download: {}'.format(pattern))

    x0 = x0.pop()
    x1 = os.path.join(DOT_MODULE_CACHE_ROSTER, address, datetime.now().isoformat() + '.' + format)
    util.mkdir_p(os.path.dirname(x1))
    shutil.move(x0, x1)

    return x1



from operator import itemgetter
import openpyxl
import csv

def roster_xlsx_parse(source):
    
    wb = openpyxl.load_workbook(source)
    ws = wb.active

    def g():
        for row in ws.rows:
            yield [x.value for x in row]
    rows = list(g())

    wb.close()

    rows = rows[2:]
    
    fieldnames = [str(x) for x in rows[0]]
    def g():
        for row in rows[1:]:
            if row[0] is None:
                continue
            yield {x: str(y) for x, y in zip(fieldnames, row)}
    rows = sorted(g(), key=itemgetter('Last Name', 'First Name', 'NetId'))

    def g():
        for row in rows:
            if row['Units'].startswith('D'):
                continue
            yield row

    return fieldnames, g()

def roster_xlsx_to_csv(source, target):
    fieldnames, it = roster_xlsx_parse(source)
    with open(target, 'w') as w:
        writer = csv.DictWriter(w, fieldnames)
        writer.writeheader()
        writer.writerows(it)


import sys
import json
import apsw

SCHEMA = os.path.join(os.path.dirname(__file__), 'schema.sql')
PRAGMA = os.path.join(os.path.dirname(__file__), 'pragma.sql')

DB = os.path.join(DOT_MODULE_CACHE, 'db.sqlite')

def row_factory(cur, row):
    return {k[0]: row[i] for i, k in enumerate(cur.getdescription())}

def exec_trace(cur, sql, bindings):
    print('sql     :', sql)
    print('bindings:', bindings)
    return True

def drop_triggers_and_views(con):
    with con:
        cur = con.cursor()
        sql = '''SELECT * FROM sqlite_master WHERE type IN ('trigger', 'view');'''
        rows = list(cur)
        for row in rows:
            t = row['type'].upper()
            assert t in ['TRIGGER', 'VIEW',]
            n = row['name']
            assert not '"' in name, '{t} names are not allowed to contain a double-quote ": {n}'.format(t=t, n=n)
            cur.execute('''DROP {t} "{n}";'''.format(t=t, n=n))

def _print(*args):
    print(*args)

def connection_hook(con):
    drop_triggers_and_views(con)
    con.enableloadextension(True)
    
    con.createscalarfunction("print", _print)

    cur = con.cursor()

    con.setrowtrace(row_factory)
    #con.setexectrace(exec_trace)
    with con:
        with open(SCHEMA, 'r') as r: 
            for piece in r.read().split('\n--\n'):
                #print('-'*80)
                #print(piece)
                cur.execute(piece)
    with open(PRAGMA, 'r') as r: 
        cur.execute(r.read())

apsw.connection_hooks.append(connection_hook)


def db_connect():
    return apsw.Connection(DB)


def yys_to_2yym(x):
    yy = x[:2]
    s = x[2]
    return '2' + yy + dict(s='2', u='5', f='8')[s]



import re

def _db_update_search(con, cur):

    def g():
        if not os.path.exists(DOT_MODULE_CACHE_SEARCH): return
        for dirpath, subdirs, files in os.walk(DOT_MODULE_CACHE_SEARCH):
            for x in files:
                if x.endswith(".json"):
                    yield os.path.join(dirpath, x)
    X = sorted(g())

    cbaddress_re = re.compile(r'(?P<prefix>[a-z]+)(?P<number>[a-z0-9]{4})\.(?P<section>[a-z0-9]{3})\.(?P<term>[0-9]{2}[suf])')

    def g():
        for x in X:
            with open(x, 'r') as r:
                Y = json.load(r)
            for course in Y['report_data']:
                address = course['section_address'].lower().strip()
                m = cbaddress_re.match(address)
                if m is None:
                    print('non-matching cbaddress:', address)
                    continue
                d = m.groupdict()
                term = yys_to_2yym(d['term'])
                prefix = d['prefix']
                number = d['number']
                title = course['title'] or None
                section = d['section']
                activity = course['activity_type'].lower() or None
                yield dict(term=term, prefix=prefix, number=number, title=title, section=section, activity=activity)

    with con:
        sql = (
                '''INSERT INTO "course*" (prefix, number, title) '''
                '''VALUES (:prefix, :number, :title) '''
                '''ON CONFLICT DO NOTHING '''
                ''';'''

                '''INSERT INTO "section*" (term, prefix, number, section, activity) '''
                '''VALUES (:term, :prefix, :number, :section, :activity) '''
                '''ON CONFLICT DO NOTHING '''
                ''';'''
                )

        rows = sorted(g(), key=itemgetter('term'))
        cur.executemany(sql, rows)

from copy import copy

def _db_update_roster(con, cur):

    def g():
        if not os.path.exists(DOT_MODULE_CACHE_ROSTER): return
        for dirpath, subdirs, files in os.walk(DOT_MODULE_CACHE_ROSTER):
            for x in files:
                if x.endswith(".json"):
                    yield os.path.join(dirpath, x)
    X = sorted(g())

    def to_dict(x):
        x = os.path.dirname(x)
        x = os.path.basename(x)
        term, prefix, number, section = x.split('-')
        return dict(term=yys_to_2yym(term), prefix=prefix, number=number, section=section)

    def g():
        for x in X:
            yield to_dict(x)

    with con:
        sql = (
                '''INSERT INTO "course*" (prefix, number) '''
                '''VALUES (:prefix, :number) '''
                '''ON CONFLICT DO NOTHING '''
                ''';'''

                '''INSERT INTO "section*" (term, prefix, number, section, activity) '''
                '''VALUES (:term, :prefix, :number, :section, NULL) '''
                '''ON CONFLICT DO NOTHING '''
                ''';'''
                )
        rows = sorted(g(), key=itemgetter('term'))
        cur.executemany(sql, rows)

    def g():
        K = ['netid', 'last_name', 'middle_name', 'first_name',]
        for x in X:
            row0 = to_dict(x)
            with open(x, 'r') as r:
                y = json.load(r)
            for row1 in y['report_data']:
                for k in K:
                    row1[k] = row1[k].strip()
                if not row1['netid']:
                    print('missing netid:', row1, file=sys.stderr)
                    continue
                row2 = copy(row0)
                for k in K:
                    row2[k] = row1[k]
                yield row2

    with con:
        sql = (
                '''INSERT INTO "netid" (netid, "last_name", "middle_name", "first_name") '''
                '''VALUES (:netid, :last_name, :middle_name, :first_name) '''
                '''ON CONFLICT DO NOTHING '''
                ''';'''

                '''INSERT INTO "student+section*" (term, prefix, number, section, netid) '''
                '''VALUES (:term, :prefix, :number, :section, :netid) '''
                '''ON CONFLICT DO NOTHING '''
                ''';'''
                )
        rows = sorted(g(), key=itemgetter('term', 'netid'))
        cur.executemany(sql, rows)



def alias():

    con = db_connect()
    cur = con.cursor()

    _db_update_search(con, cur)
    _db_update_roster(con, cur)

    con.close()




def db_update():

    util.mkdir_p(os.path.dirname(DB))
    con = db_connect()
    cur = con.cursor()

    _db_update_search(con, cur)
    _db_update_roster(con, cur)

    con.close()


def db_netid_to_address(netid: str):

    con = apsw.Connection(DB)
    cur = con.cursor()

    with con:
        sql = (
                '''SELECT address FROM "student+section*" '''
                '''WHERE netid = :netid '''
                ''';'''
                )
        cur.execute(sql, dict(netid=netid))
        return [x['address'] for x in cur]

