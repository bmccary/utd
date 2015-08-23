
from setuptools import setup

setup(
        name='utd',
        version='0.1',
        description='Utilities for the UTD Math Department',
        url='http://github.com/bmccary/utd',
        author='Brady McCary',
        author_email='brady.mccary@gmail.com',
        license='MIT',
        packages=['utd'],
        install_requires=[
                'csvu',
                'selenium',
                'numberjack',
            ],
        scripts=[
                    'bin/utd-coursebook-roster-fetch',
                    'bin/utd-util-dates',
                    'bin/utd-schedule-coursebook-fetch',
                    'bin/utd-schedule-xlsx-coursebook-splice',
                    'bin/utd-schedule-xlsx-update',
                ],
        zip_safe=False
    )

