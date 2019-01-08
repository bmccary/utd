
import re
from subprocess import Popen, PIPE, TimeoutExpired
from operator import itemgetter

from pytypes import typechecked

SEARCH_RE = re.compile(r'^[A-Za-z0-9]+$')

FILTER = '(&(objectClass=person)(|(cn=*{term}*)(displayName=*{term}*)(givenName=*{term}*)(sn=*$@*)(mail=*{term}*)(canonicalMailAddress=*{term}*)(uid=*{term}*)))'

KEYS0 = ['mail', 'canonicalMailAddress', 'sn', 'givenName', 'uid',]
EXTRA = ['title', 'dept', 'major', 'class', 'degree', 'career', 'telephoneNumber', 'office', 'mailstop',]
KEYS = KEYS0 + EXTRA

class LDAPReturnCodeException(Exception):
    def __init__(self, code):
        self.code = code

@typechecked
def search(term: str, max: int = 100, timeout: int = 10, verbose: bool = False):
    assert SEARCH_RE.match(term), 'Expected :term to match the regular expression "{}": {}'.format(SEARCH_RE.pattern, term)
    args = [
            'ldapsearch',
            '-x',
            '-z', str(max),
            '-l', str(timeout),
            FILTER.format(term=term),
        ] + KEYS
    if verbose:
        print('Generated LDAP command: ' + ' '.join(args))
    p = Popen(args, stdout=PIPE)
    stdout, stderr = p.communicate(timeout=timeout + 5)
    if stdout: stdout = stdout.decode('utf-8')
    if stderr: stderr = stderr.decode('utf-8')
    if p.returncode != 0: 
        if verbose:
            print('\nstdout', '-'*80, '\n', stdout)
            print('\nstderr', '-'*80, '\n', stderr)
        raise LDAPReturnCodeException(code=p.returncode)
    def g():
        d = dict()
        for line in stdout.split('\n'):
            line = line.strip()
            if not line: continue
            if line.startswith('#'): continue
            key, val = [u.strip() for u in line.split(':')]
            if key == 'dn': 
                if len(d) > 0:
                    yield d
                    d = dict()
                continue
            if key in KEYS:
                d[key] = val
        if len(d) > 0:
            yield d
    return sorted(g(), key=itemgetter('sn', 'givenName', 'uid'))

