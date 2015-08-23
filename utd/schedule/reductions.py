
import dateutil
import dateutil.parser
import datetime
import calendar

MONDAY = datetime.datetime(year=1970, month=1, day=5)
DT     = datetime.timedelta(days=1)
DAYS   = [MONDAY + DT*i for i in range(7)]

DAYSs = [
            'MON',
            'TUES',
            'WED',
            'THURS',
            'FRI',
            # FIXME: Saturday and Sunday currently unknown
        ]

NOSCHEDULE = '-schedule is not posted or not applicable-'.upper()

KIND_EXAM  = 'EXM'
KIND_LAB   = 'LAB'

def schedule(row):
    """
    Explanation.

    1970-01-05 is the first Monday after the beginning
    of the UNIX epoch (1970-01-01, a Thursday). The schedule 
    computed here uses the convenient fiction that the week we are 
    referring to is this first full week of the UNIX epoch, with 
    time recorded in seconds. The purpose of this fiction is
    that we are going to perform a constraint satisfaction
    and optimization problem. We are using seconds since the 
    UNIX epoch as the time unit.
    """

    x = row['schedule_cb'].strip().upper()

    if not x or x == NOSCHEDULE:
        return None

    x = x.split(';')
    x = x[0]

    """
    Examples.

    Mon, Wed & Fri : 10:00am-10:50am : CB3_1.312
    Tues & Thurs : 5:30pm-6:45pm : FO_2.208
    Wed : 1:00pm-2:50pm : CB3_1.310
    """
    
    x = [y.strip() for y in x.split(' : ')]

    days, time, _ = x

    time0s, time1s = time.split('-')

    def g():
        for i, d in enumerate(DAYSs):
            if days.find(d) < 0:
                continue

            # Parse time relative to DOW.
            time0 = dateutil.parser.parse(time0s, default=DAYS[i])
            time1 = dateutil.parser.parse(time1s, default=DAYS[i])

            # Convert to seconds since UNIX epoch.
            time0 = calendar.timegm(time0.timetuple())
            time1 = calendar.timegm(time1.timetuple())

            yield (time0, time1)

    x = ','.join('{time0}-{time1}'.format(time0=time0, time1=time1) for time0, time1 in g())

    return x            


def courses(row):
    human = row['courses_human'].upper().strip().replace('\t', ' ')
    for i in xrange(5):
        human = human.replace('  ', ' ')
    def gen():
        prefix = None
        for x in human.split(','):
            y = x.strip().split(' ')
            if len(y) == 1:
                if prefix is None:
                    raise Exception('Cannot parse 1: {}'.format(row['courses_human']))
                yield (prefix, y[0])
            elif len(y) == 2:
                prefix, y = y
                yield (prefix, y)
            else:
                raise Exception('Cannot parse 2: {}'.format(row['courses_human']))
    return ', '.join('{} {}'.format(prefix, y) for prefix, y in gen())

