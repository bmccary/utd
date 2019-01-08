
import os
from prettytable import PrettyTable
from operator import itemgetter
import click

from . import config

@click.group()
def cli():
    pass



from .ldap import search as ldap_search, KEYS as LDAP_KEYS, LDAPReturnCodeException

@cli.command(name='ldap', help='Perform an LDAP search.')
@click.option('--max', '-m', type=click.IntRange(0, 100), default=0, help='Maximum number of responses (0 means unlimited).')
@click.option('--timeout', '-t', type=click.IntRange(2, 30), default=5, help='Timeout, in seconds.')
@click.option('--verbose/--no-verbose', default=False)
@click.argument('term', type=click.STRING)
def cli_ldap(max, timeout, term, verbose):
    try:
        rows = list(ldap_search(term=term, max=max, timeout=timeout, verbose=verbose))
        if len(rows) > 0:
            fieldnames = LDAP_KEYS
            table = PrettyTable(fieldnames)
            table.align = 'l'
            for row in rows:
                table.add_row([row.get(k, '') for k in fieldnames])
            print(table.get_string())
    except LDAPReturnCodeException as e:
        raise click.ClickException('There was an LDAP Exception (code = {}). Try running again with --verbose.'.format(e.code))




@cli.group(name='coursebook')
def cli_coursebook():
    pass




@cli_coursebook.group(name='db')
def cli_coursebook_db():
    pass

@cli_coursebook_db.command(name='update')
def cli_coursebook_db_update():
    coursebook.db_update()

@cli_coursebook_db.command(name='netid-to-address')
@click.argument('netid', type=click.STRING)
def cli_coursebook_db_netid_to_address(netid):
    X = list(coursebook.db_netid_to_address(netid))
    if X:
        click.echo(' '.join(X))




@cli_coursebook.group(name='roster')
def cli_coursebook_roster():
    pass

@cli_coursebook_roster.command(name='xlsx-to-csv', help='Convert a CourseBook roster XLSX to CSV.')
@click.option('--force/--no-force', default=False, help="Overwrite existing file.")
@click.argument('source', type=click.Path(exists=True))
@click.argument('target', type=click.Path())
def cli_coursebook_xlsx_to_csv(force, source, target):
    if os.path.exists(target) and not force:
        raise click.ClickException('File exists, maybe use --force?: ' + target)
    coursebook.roster_xlsx_to_csv(source, target)

@cli_coursebook_roster.group(name='download')
def cli_coursebook_roster_download():
    pass

import shutil

from . import coursebook

@cli_coursebook_roster.command(name='download', help='Download a CourseBook roster.')
@click.option('--force/--no-force', default=False, help="Overwrite existing file.")
@click.option('--new/--no-new', default=False, help="Get a new file (don't use the cache).")
@click.option('--get-password', default=None, help='Command to evaluate to get password (default is to ask).')
@click.option('--netid', default=None, help='Use this NetID.')
@click.argument('address', nargs=-1, type=click.STRING)
def cli_coursebook_roster_download(netid, get_password, new, force, address):

    for x in address:
        if os.path.exists(x) and not force:
            raise click.ClickException('File exists, maybe use --force?: ' + x)

    if netid is None: netid = config.netid
    if get_password is None: get_password = config.get_password

    if netid is None:
        raise click.ClickException('You must either specify a NetID in {config} or with --netid.'.format(config.CONFIG_FILE))

    for x in address:
        y, f = os.path.splitext(x)
        f = f[1:]
        if not (f in coursebook.ROSTER_FORMAT):
            raise click.ClickException("{}: I don't know how to download a {}, only: {}.".format(x, f, str(coursebook.ROSTER_FORMAT)))
        z = coursebook.roster_download(netid=netid, get_password=get_password, address=y, format=f, new=new)
        shutil.copyfile(z, x)




