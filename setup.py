from setuptools import setup, find_packages
import os

version = '0.0.1'

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.rst')).read()
except IOError:
    README = ''

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
      packages=find_packages(exclude=['ez_setup']),
      include_package_data=True,
      tests_require = ['mock', 'pymongo >= 2.7', 'boto'],
      test_suite='nose.collector',
      zip_safe=False,
)
