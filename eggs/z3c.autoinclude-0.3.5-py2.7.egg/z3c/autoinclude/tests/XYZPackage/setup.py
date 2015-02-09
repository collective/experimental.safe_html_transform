from setuptools import setup, find_packages

version = '0.1'

setup(name='XYZPackage',
      version=version,
      description="",
      long_description="""\
""",
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Zope3",
        "Programming Language :: Python",
        ],
      keywords='',
      author='',
      author_email='',
      url='',
      license="''",
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['x', 'x.y'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
	  'TestDirective',
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
