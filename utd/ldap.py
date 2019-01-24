
import re
from typing import List
from collections import OrderedDict

import ldap

WORD_RE = re.compile(r'^[-.+A-Za-z0-9]+$')

URI = 'ldaps://nsldap2.utdallas.edu'
BASE = 'dc=utdallas,dc=edu'
LDAP = None

def _LDAP():
    global LDAP
    if LDAP is None:
        LDAP = ldap.initialize(URI)
    return LDAP

NETID_KEY = 'uid'
ALIAS_KEY = 'pea'

KNOWN_KEYS = \
    [
        'cn', 
        'displayName', 
        'homeDirectory', 
        'pea', 
        'dept', 
        'telephoneNumber', 
        'pat', 
        'office', 
        'title', 
        'sn', 
        'mailstop', 
        'smbHomeDirectory', 
        'gidNumber', 
        'uidNumber', 
        'canonicalMailAddress', 
        'autosetpea', 
        'givenName', 
        'gecos', 
        'eduPersonAffiliation', 
        'eduPersonScopedAffiliation', 
        'loginShell', 
        'objectClass', 
        'jamsid', 
        'uid', 
        'mail', 
        'majorName', 
        'major', 
        'collegeName', 
        'college', 
        'initials', 
        'degree', 
        'class', 
        'career',
    ]

def _decode(X):
    def g():
        for k in X:
            if k.endswith(';binary'):
                yield k, X[k][0]
            else:
                yield k, X[k][0].decode()
    return dict(g())

def _raise_word(word: str, thing: str = 'input'):
    if not WORD_RE.match(word):
        raise Exception('Expected {thing} to match pattern `{pattern}`: {word}'.format(thing=thing, pattern=WORD_RE.pattern, word=word))

def _raise_keys(keys: List[str] = None):
    if keys:
        for k in keys:
            _raise_word(k, 'keys')

def _filter_by_keys(rows, keys: List[str] = None):
    if keys:
        for row in rows:
            yield OrderedDict((k, row.get(k)) for k in keys)
    else:
        yield from rows



def filter(filter_: str, keys: List[str] = None):
    _raise_keys(keys)
    def g():
        for _, entry in _LDAP().search_s(BASE, ldap.SCOPE_SUBTREE, filter_):
            yield _decode(entry)
    return list(_filter_by_keys(g(), keys))




SEARCH_FILTER = '(& (objectClass=person) (| (cn=*{term}*) (displayName=*{term}*) (givenName=*{term}*) (sn=*$@*) (mail=*{term}*) (canonicalMailAddress=*{term}*) (uid=*{term}*)))'

def search(term: str, keys: List[str] = None):
    _raise_word(term, ':term')
    filter_ = SEARCH_FILTER.format(term=term)
    return filter(filter_, keys)



NETID_FILTER = '(& (objectClass=person) ({k}={{netid}}))'.format(k=NETID_KEY)

def netid(netid_: str, keys: List[str] = None):
    _raise_word(netid_, ':netid_')
    filter_ = NETID_FILTER.format(netid=netid_)
    rows = filter(filter_, keys)
    assert len(rows) < 2, rows
    if rows: return rows[0]

def netid_to_alias(netid_: str):
    row = netid(netid_, [ALIAS_KEY,])
    if not row: return
    x = row[ALIAS_KEY]
    assert '@' in x, x
    return x.split('@')[0]



ALIAS_FILTER = '(& (objectClass=person) ({k}={{alias}}@utdallas.edu))'.format(k=ALIAS_KEY)

def alias(alias_: str, keys: List[str] = None):
    _raise_word(alias_, ':alias_')
    filter_ = ALIAS_FILTER.format(alias=alias_)
    rows = filter(filter_, keys)
    assert len(rows) < 2, rows
    if rows: return rows[0]

def alias_to_netid(alias_: str):
    row = alias(alias_, [NETID_KEY,])
    if not row: return
    x = row[NETID_KEY]
    return x

