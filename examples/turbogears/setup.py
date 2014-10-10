# -*- coding: utf-8 -*-
#quickstarted Options:
#
# sqlalchemy: True
# auth:       sqlalchemy
# mako:       False
#
#

#This is just a work-around for a Python2.7 issue causing
#interpreter crash at exit when trying to log an info message.
try:
    import logging
    import multiprocessing
except:
    pass

import sys
py_version = sys.version_info[:2]

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

testpkgs=['WebTest >= 1.2.3',
               'nose',
               'coverage',
               'gearbox'
               ]

install_requires=[
    "TurboGears2 >= 2.3.2",
    "Genshi",
    "zope.sqlalchemy >= 0.4",
    "sqlalchemy",
    "alembic",
    "repoze.who",
    "tw2.forms",
    "tgext.admin >= 0.6.1",
    ]

setup(
    name='depotexample',
    version='0.1',
    description='',
    author='',
    author_email='',
    #url='',
    packages=find_packages(exclude=['ez_setup']),
    install_requires=install_requires,
    include_package_data=True,
    test_suite='nose.collector',
    tests_require=testpkgs,
    package_data={'depotexample': ['i18n/*/LC_MESSAGES/*.mo',
                                 'templates/*/*',
                                 'public/*/*']},
    message_extractors={'depotexample': [
            ('**.py', 'python', None),
            ('templates/**.html', 'genshi', None),
            ('public/**', 'ignore', None)]},

    entry_points={
        'paste.app_factory': [
            'main = depotexample.config.middleware:make_app'
        ],
        'gearbox.plugins': [
            'turbogears-devtools = tg.devtools'
        ]
    },
    zip_safe=False
)
