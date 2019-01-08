
from setuptools import setup, find_packages

setup(
        name='utd',
        version='1.0',
        description='UTD Tools',
        url='http://github.com/bmccary/utd',
        author='Brady McCary',
        author_email='brady.mccary@gmail.com',
        license='MIT',
        packages=find_packages(),
        install_requires=[
                'apsw',
                'click',
            ],
        include_package_data=True,
        entry_points='''
            [console_scripts]
            utd=utd.script:cli
            ''',
    )

