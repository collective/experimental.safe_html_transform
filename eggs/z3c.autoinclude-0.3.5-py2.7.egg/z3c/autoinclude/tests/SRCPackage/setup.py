from setuptools import setup, find_packages
import sys, os

version = '0.0'

setup(name='SRCPackage',
      version=version,
      description="",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='',
      author_email='',
      url='',
      license='',
      package_data = {'': ['*.zcml',]},
      packages=find_packages('src', exclude=['ez_setup', 'examples', 'tests']),
      package_dir={'': 'src'},
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        'BCPackage',
	'z3c.autoinclude',
	'TestDirective',
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
