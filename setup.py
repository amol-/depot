from setuptools import setup, find_packages
import os, sys

version = '0.1.2'

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
except IOError:
    README = ''

TEST_DEPENDENCIES = ['mock',
                     'pymongo >= 2.7',
                     'sqlalchemy',
                     'pillow',
                     'ming',
                     'TurboGears2',
                     'WebTest']

py_version = sys.version_info[:2]
if py_version != (3, 2):
    TEST_DEPENDENCIES += ['boto', 'coverage']
else:
    TEST_DEPENDENCIES += ['coverage < 4.0']


INSTALL_DEPENDENCIES = ['unidecode']
if py_version == (2, 6):
    INSTALL_DEPENDENCIES += ['importlib']

setup(name='filedepot',
      version=version,
      description="Toolkit for storing files and attachments in web applications",
      long_description=README,
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Environment :: Web Environment",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 2"
        ],
      keywords='storage files s3 gridfs mongodb aws sqlalchemy wsgi',
      author='Alessandro Molina',
      author_email='alessandro.molina@axant.it',
      url='https://github.com/amol-/depot',
      license='MIT',
      packages=find_packages(exclude=['ez_setup', 'tests']),
      include_package_data=True,
      install_requires=INSTALL_DEPENDENCIES,
      tests_require=TEST_DEPENDENCIES,
      extras_require={
         # Used by Travis and Coverage due to setup.py nosetests
         # causing a coredump when used with coverage
         'testing': TEST_DEPENDENCIES,
      },
      test_suite='nose.collector',
      zip_safe=False,
)
